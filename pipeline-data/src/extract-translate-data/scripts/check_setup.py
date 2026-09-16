import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo import được module từ thư mục gốc
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_io import read_yaml_config
from shared.logger import get_logger

def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    logger = get_logger("check_setup")
    
    print("=== KIỂM TRA MÔI TRƯỜNG ===")
    all_ok = True
    
    # 1. Kiểm tra config.yaml
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ Thiếu file config.yaml")
        logger.error("Missing config.yaml")
        all_ok = False
    else:
        try:
            config = read_yaml_config(config_path)
            print("✅ File config.yaml hợp lệ")
        except Exception as e:
            print(f"❌ Lỗi đọc config.yaml: {e}")
            logger.error(f"Error reading config.yaml", extra={"meta": {"error": str(e)}})
            all_ok = False

    # 2. Kiểm tra các key trong .env (chỉ còn GEMINI_API_KEY)
    # Kiểm tra đặc biệt cho GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY1") and not os.getenv("GEMINI_API_KEY"):
        print("❌ Thiếu biến môi trường GEMINI_API_KEY / GEMINI_API_KEY1")
        logger.error("Missing GEMINI_API_KEY")
        all_ok = False
    else:
        print("✅ Đã cấu hình: GEMINI_API_KEY")
            
    if all_ok:
        print("\n🎉 Môi trường đã sẵn sàng!")
        logger.info("Setup check passed successfully.")
        sys.exit(0)
    else:
        print("\n⚠️ Vui lòng bổ sung các thành phần còn thiếu.")
        logger.warning("Setup check failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
