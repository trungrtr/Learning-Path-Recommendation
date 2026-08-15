"""Tạo dữ liệu và fine-tune UniSkill nội bộ trên quan hệ ESCO của 30 ngành nghề."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG, SkillMatchingConfig, load_skill_matching_config


def build_weak_training_pairs(config: SkillMatchingConfig) -> int:
    """Tạo positive/negative pairs từ occupation descriptions và ESCO skill relations IT-30.

    Đây là weak supervision theo 30 nghề: positive là skill thuộc quan hệ essential với nghề;
    negative được lấy từ skill không thuộc nghề đó. Dataset chỉ dùng artifact nội bộ và là
    bootstrap cho model; có thể thay bằng course-skill labels đã gán nhãn khi có dữ liệu thật.
    """
    with config.esco_occupations_csv.open(encoding="utf-8-sig", newline="") as source:
        occupations = {row["occupation_id"]: row for row in csv.DictReader(source)}
    with config.esco_skills_csv.open(encoding="utf-8-sig", newline="") as source:
        skills = {row["skill_id"]: row for row in csv.DictReader(source)}
    with config.esco_relations_csv.open(encoding="utf-8-sig", newline="") as source:
        relations = list(csv.DictReader(source))

    relation_skill_ids: dict[str, set[str]] = {occupation_id: set() for occupation_id in occupations}
    for relation in relations:
        if relation.get("relationType") == "essential" and relation.get("occupation_id") in relation_skill_ids:
            relation_skill_ids[relation["occupation_id"]].add(relation["skill_id"])

    randomizer = random.Random(config.training_seed)
    all_skill_ids = sorted(skills)
    pairs: list[dict[str, Any]] = []
    for occupation_id, positive_ids in relation_skill_ids.items():
        occupation = occupations[occupation_id]
        context = f"{occupation['occupation_label']} {occupation.get('occupation_description') or ''}".strip()
        negative_ids = [skill_id for skill_id in all_skill_ids if skill_id not in positive_ids]
        for skill_id in sorted(positive_ids):
            pairs.append({"text_en": context, "skill_uri": skills[skill_id]["skill_uri"], "skill_label": skills[skill_id]["skill_label"], "label": 1})
            for negative_id in randomizer.sample(negative_ids, k=min(config.negatives_per_positive, len(negative_ids))):
                pairs.append({"text_en": context, "skill_uri": skills[negative_id]["skill_uri"], "skill_label": skills[negative_id]["skill_label"], "label": 0})

    randomizer.shuffle(pairs)
    config.training_pairs_path.parent.mkdir(parents=True, exist_ok=True)
    with config.training_pairs_path.open("w", encoding="utf-8") as target:
        for pair in pairs:
            target.write(json.dumps(pair, ensure_ascii=False) + "\n")
    return len(pairs)


def fine_tune_uniskill_it30(config: SkillMatchingConfig) -> None:
    """Fine-tune checkpoint nội bộ từ weak pairs và ghi model production vào resources/models.

    Hàm không tải hay đọc model từ ngoài project: seed checkpoint, vocabulary ESCO và training
    pairs đều nằm trong ``create_knowledge_graph_pipline``.
    """
    if not config.training_pairs_path.exists():
        raise FileNotFoundError("Chưa có training pairs; hãy chạy build_weak_training_pairs trước.")
    if not config.uniskill_seed_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy UniSkill seed nội bộ: {config.uniskill_seed_dir}")
    try:
        import torch
        from torch.utils.data import DataLoader
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("Thiếu torch hoặc transformers để fine-tune UniSkill IT-30.") from exc

    pairs = [json.loads(line) for line in config.training_pairs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not pairs:
        raise ValueError("Training pairs rỗng.")
    device = config.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(config.uniskill_seed_dir)
    model = AutoModelForSequenceClassification.from_pretrained(config.uniskill_seed_dir).to(device)

    def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
        encoded = tokenizer(
            [item["text_en"] for item in batch],
            [item["skill_label"] for item in batch],
            padding=True,
            truncation=True,
            max_length=config.max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor([item["label"] for item in batch], dtype=torch.long)
        return encoded

    loader = DataLoader(pairs, batch_size=config.training_batch_size, shuffle=True, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.training_learning_rate)
    model.train()
    for epoch in range(config.training_epochs):
        for step, batch in enumerate(loader, start=1):
            batch = {key: value.to(device) for key, value in batch.items()}
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            if step % 25 == 0 or step == len(loader):
                print(f"Epoch {epoch + 1}/{config.training_epochs}, step {step}/{len(loader)}, loss {loss.item():.4f}", flush=True)
    config.uniskill_model_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(config.uniskill_model_dir)
    tokenizer.save_pretrained(config.uniskill_model_dir)
    (config.uniskill_model_dir / "training_metadata.json").write_text(
        json.dumps(
            {
                "training_pairs": len(pairs),
                "epochs": config.training_epochs,
                "negatives_per_positive": config.negatives_per_positive,
                "source": "ESCO IT-30 essential occupation-skill relations",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    """CLI xây dataset và/hoặc fine-tune UniSkill IT-30 hoàn toàn nội bộ."""
    parser = argparse.ArgumentParser(description="Build weak data and fine-tune internal UniSkill IT-30.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--build-pairs", action="store_true")
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    config = load_skill_matching_config(args.config)
    if args.build_pairs:
        print(f"Built weak training pairs: {build_weak_training_pairs(config)}")
    if args.train:
        fine_tune_uniskill_it30(config)
        print(f"Saved internal fine-tuned model: {config.uniskill_model_dir}")
    if not args.build_pairs and not args.train:
        parser.error("Chọn --build-pairs, --train hoặc cả hai.")


if __name__ == "__main__":
    main()
