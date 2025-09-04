# fix_anchors.py - 기존 템플릿의 앵커를 라벨 기반으로 자동 개선

import json
import os

def fix_template_anchors(template_file="templates.json"):
    """기존 템플릿의 앵커를 라벨 기반으로 자동 개선"""
    
    if not os.path.exists(template_file):
        print(f"❌ {template_file} 파일을 찾을 수 없습니다.")
        return
    
    # 백업 생성
    backup_file = f"{template_file}.backup_anchor_fix"
    
    with open(template_file, 'r', encoding='utf-8') as f:
        templates = json.load(f)
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 백업 생성: {backup_file}")
    
    fixed_count = 0
    
    for template_name, template_data in templates.items():
        print(f"\n🔧 {template_name} 앵커 개선 중...")
        
        if "rois" not in template_data:
            continue
            
        for roi_name, roi_info in template_data["rois"].items():
            if "coords" not in roi_info:
                continue
                
            roi_coords = roi_info["coords"]
            roi_left, roi_top, roi_right, roi_bottom = roi_coords
            
            # 기존 앵커 정보
            old_anchor = roi_info.get("anchor_coords", [])
            
            # 새로운 라벨 기반 앵커 생성
            label_width = min(80, roi_left)  # 80px 또는 페이지 경계까지
            
            new_anchor_coords = [
                max(0, roi_left - label_width),  # 페이지 경계 제한
                roi_top - 5,    # ROI보다 약간 위
                roi_left - 3,   # ROI 직전까지  
                roi_bottom + 5  # ROI보다 약간 아래
            ]
            
            # 앵커 개선 정보 출력
            old_size = f"{old_anchor[2]-old_anchor[0]:.1f}x{old_anchor[3]-old_anchor[1]:.1f}" if old_anchor else "없음"
            new_size = f"{new_anchor_coords[2]-new_anchor_coords[0]:.1f}x{new_anchor_coords[3]-new_anchor_coords[1]:.1f}"
            
            print(f"   {roi_name}: {old_size} → {new_size} (라벨 영역)")
            
            # 앵커 좌표 업데이트
            roi_info["anchor_coords"] = new_anchor_coords
            fixed_count += 1
    
    # 수정된 템플릿 저장
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 완료: {fixed_count}개 앵커가 라벨 기반으로 개선되었습니다.")
    print(f"📁 원본 백업: {backup_file}")
    print(f"🎯 개선 효과: 앵커가 ROI 좌측 라벨 영역으로 변경되어 스캔 문서 매칭률이 크게 향상될 것입니다!")

if __name__ == "__main__":
    fix_template_anchors()
