# batch_validator.py

import os
import json
import time
from src.pdf_validator_gui import PDFValidator
from src.folder_manager import FolderManager

# --- 설정 ---
INPUT_DIR = "input"
TEMPLATES_FILE = "templates.json"
# ------------

def load_templates():
    """templates.json 파일에서 모든 템플릿을 로드합니다."""
    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)
            print(f"✅ 템플릿 {len(templates)}개를 성공적으로 불러왔습니다.")
            return templates
    except FileNotFoundError:
        print(f"❌ 오류: '{TEMPLATES_FILE}' 파일을 찾을 수 없습니다.")
        print("    먼저 템플릿 설정 도구를 사용하여 템플릿을 하나 이상 저장해야 합니다.")
        return None
    except json.JSONDecodeError:
        print(f"❌ 오류: '{TEMPLATES_FILE}' 파일의 형식이 잘못되었습니다.")
        return None

def run_batch_validation():
    """input 폴더 내의 모든 PDF를 자동으로 검증합니다."""
    print("\n🚀 PDF 문서 일괄 검증 시스템을 시작합니다.")
    print("=" * 60)

    # 1. 템플릿 로드
    templates = load_templates()
    if not templates:
        return

    # 2. Input 폴더 구조 확인 및 처리
    if not os.path.exists(INPUT_DIR):
        print(f"📂 '{INPUT_DIR}' 폴더를 생성합니다. 검증할 PDF 파일을 보험사별 폴더에 넣어주세요.")
        os.makedirs(INPUT_DIR)
        return

    folder_manager = FolderManager()
    total_files_processed = 0
    total_start_time = time.time()

    # input 폴더 내의 보험사별 폴더 순회
    for company_name in os.listdir(INPUT_DIR):
        company_input_path = os.path.join(INPUT_DIR, company_name)
        if not os.path.isdir(company_input_path):
            continue

        # 3. 해당 보험사에 맞는 템플릿 찾기
        if company_name not in templates:
            print(f"⚠️ 경고: '{company_name}' 폴더에 해당하는 템플릿을 찾을 수 없습니다. 건너뜁니다.")
            continue

        template_data = templates[company_name]
        print(f"\n🏢 '{company_name}' 보험사 폴더 검증을 시작합니다. (템플릿: '{company_name}')")

        # 4. 폴더 내 PDF 파일 순차 검증 (Queue)
        pdf_files = [f for f in os.listdir(company_input_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("  - 검증할 PDF 파일이 없습니다.")
            continue

        validator = PDFValidator(template_data)

        for pdf_file in pdf_files:
            filled_pdf_path = os.path.join(company_input_path, pdf_file)
            file_start_time = time.time()
            total_files_processed += 1
            print(f"  - 📄 '{pdf_file}' 검증 중...")

            try:
                # 5. 검증 실행
                results = validator.validate_pdf(filled_pdf_path)

                # 6. 결과 분석 및 저장
                deficient_fields = sum(1 for r in results if r['status'] == 'DEFICIENT')
                result_type = "fail" if deficient_fields > 0 else "success"

                # 주석이 달린 PDF 생성
                output_dir = folder_manager.get_output_path(company_name, template_name=company_name, result_type=result_type)
                base_name = os.path.splitext(pdf_file)[0]
                output_filename = f"review_{base_name}_{int(time.time())}.pdf"
                output_path = os.path.join(output_dir, output_filename)

                validator.create_annotated_pdf(filled_pdf_path, output_path)

                processing_time = time.time() - file_start_time
                if result_type == "fail":
                    print(f"    ❌ 검증 실패 ({deficient_fields}개 항목 미비). 결과 저장: {output_path} ({processing_time:.2f}초)")
                else:
                    print(f"    ✅ 검증 성공. 결과 저장: {output_path} ({processing_time:.2f}초)")

            except Exception as e:
                print(f"    🔥 '{pdf_file}' 검증 중 심각한 오류 발생: {e}")

    total_processing_time = time.time() - total_start_time
    print("\n" + "=" * 60)
    print("🎉 모든 작업이 완료되었습니다.")
    print(f"   - 총 처리된 파일: {total_files_processed}개")
    print(f"   - 총 소요 시간: {total_processing_time:.2f}초")


if __name__ == "__main__":
    run_batch_validation()