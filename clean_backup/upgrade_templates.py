#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿 업그레이드 스크립트
기존 templates.json의 ROI에 앵커 정보가 없는 경우를 위한 호환성 스크립트
"""

import json
import os
import shutil
from datetime import datetime

def upgrade_templates():
    """기존 템플릿을 새로운 앵커 지원 형식으로 업그레이드"""
    
    print("🔧 템플릿 업그레이드 도구")
    print("=" * 50)
    
    # templates.json 파일 확인
    if not os.path.exists("templates.json"):
        print("❌ templates.json 파일을 찾을 수 없습니다.")
        return False
    
    # 백업 생성
    backup_name = f"templates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        shutil.copy2("templates.json", backup_name)
        print(f"✅ 백업 생성: {backup_name}")
    except Exception as e:
        print(f"❌ 백업 생성 실패: {e}")
        return False
    
    # 템플릿 로드
    try:
        with open("templates.json", 'r', encoding='utf-8') as f:
            templates = json.load(f)
        print(f"✅ 템플릿 로드 완료: {len(templates)}개 템플릿")
    except Exception as e:
        print(f"❌ 템플릿 로드 실패: {e}")
        return False
    
    # 업그레이드 통계
    upgraded_templates = 0
    upgraded_rois = 0
    
    # 각 템플릿 확인 및 업그레이드
    for template_name, template_data in templates.items():
        print(f"\n📋 템플릿 확인: {template_name}")
        
        if 'rois' not in template_data:
            print("  ⚠️ ROI 정보가 없습니다. 건너뜁니다.")
            continue
        
        rois = template_data['rois']
        template_needs_upgrade = False
        roi_count = 0
        missing_anchor_count = 0
        
        for roi_name, roi_info in rois.items():
            roi_count += 1
            
            # 앵커 정보가 없는 ROI 확인
            if 'anchor_coords' not in roi_info:
                missing_anchor_count += 1
                template_needs_upgrade = True
                
                # ROI 좌표를 앵커로 사용 (기본 호환성 처리)
                if 'coords' in roi_info:
                    # ROI 좌표의 90% 크기를 앵커로 설정
                    coords = roi_info['coords']
                    width = coords[2] - coords[0]
                    height = coords[3] - coords[1]
                    center_x = (coords[0] + coords[2]) / 2
                    center_y = (coords[1] + coords[3]) / 2
                    
                    # 90% 축소
                    new_width = width * 0.9
                    new_height = height * 0.9
                    
                    anchor_coords = [
                        center_x - new_width / 2,
                        center_y - new_height / 2,
                        center_x + new_width / 2,
                        center_y + new_height / 2
                    ]
                    
                    roi_info['anchor_coords'] = anchor_coords
                    print(f"    📌 {roi_name}: 앵커 좌표 추가됨 (ROI의 90% 크기)")
                    upgraded_rois += 1
                else:
                    print(f"    ❌ {roi_name}: 좌표 정보가 없어 앵커를 생성할 수 없습니다.")
        
        print(f"  📊 ROI 통계: 총 {roi_count}개, 앵커 없음 {missing_anchor_count}개")
        
        if template_needs_upgrade:
            upgraded_templates += 1
            print(f"  ✅ 템플릿 업그레이드 완료")
        else:
            print(f"  ✅ 이미 최신 형식입니다")
    
    # 업그레이드된 템플릿 저장
    if upgraded_templates > 0:
        try:
            with open("templates.json", 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 업그레이드 완료!")
            print(f"  📊 업그레이드된 템플릿: {upgraded_templates}개")
            print(f"  📊 업그레이드된 ROI: {upgraded_rois}개")
            print(f"  💾 백업 파일: {backup_name}")
        except Exception as e:
            print(f"\n❌ 저장 실패: {e}")
            return False
    else:
        print(f"\n✅ 모든 템플릿이 이미 최신 형식입니다.")
        # 백업 파일 삭제 (변경사항 없으므로)
        try:
            os.remove(backup_name)
            print("  🗑️ 불필요한 백업 파일 삭제됨")
        except:
            pass
    
    return True

def check_template_compatibility():
    """템플릿 호환성 확인"""
    print("\n🔍 템플릿 호환성 확인")
    print("=" * 30)
    
    if not os.path.exists("templates.json"):
        print("❌ templates.json 파일이 없습니다.")
        return
    
    try:
        with open("templates.json", 'r', encoding='utf-8') as f:
            templates = json.load(f)
    except Exception as e:
        print(f"❌ 템플릿 로드 실패: {e}")
        return
    
    total_templates = len(templates)
    compatible_templates = 0
    total_rois = 0
    anchored_rois = 0
    
    print(f"📋 총 템플릿 수: {total_templates}")
    print()
    
    for template_name, template_data in templates.items():
        if 'rois' not in template_data:
            continue
        
        rois = template_data['rois']
        template_roi_count = len(rois)
        template_anchor_count = sum(1 for roi in rois.values() if 'anchor_coords' in roi)
        
        total_rois += template_roi_count
        anchored_rois += template_anchor_count
        
        if template_anchor_count == template_roi_count:
            compatible_templates += 1
            status = "✅ 완전 호환"
        elif template_anchor_count > 0:
            status = f"⚠️ 부분 호환 ({template_anchor_count}/{template_roi_count})"
        else:
            status = "❌ 구형 템플릿"
        
        print(f"  {template_name}: {status}")
    
    print()
    print(f"📊 호환성 통계:")
    print(f"  완전 호환 템플릿: {compatible_templates}/{total_templates}")
    print(f"  앵커 보유 ROI: {anchored_rois}/{total_rois}")
    print(f"  호환성 비율: {(compatible_templates/total_templates*100):.1f}%")

def main():
    """메인 함수"""
    print("🔧 PDF Diff 템플릿 호환성 도구")
    print("Ver 1.0")
    print()
    
    # 현재 상태 확인
    check_template_compatibility()
    
    print("\n" + "="*50)
    print("업그레이드를 진행하시겠습니까?")
    print("(구형 ROI들에 자동으로 앵커 좌표를 추가합니다)")
    
    choice = input("진행 (y/n): ").lower().strip()
    
    if choice == 'y' or choice == 'yes':
        print()
        if upgrade_templates():
            print("\n🎉 템플릿 업그레이드가 완료되었습니다!")
            print("이제 PDF 검증 시 앵커 추적 기능을 사용할 수 있습니다.")
            
            # 업그레이드 후 상태 재확인
            check_template_compatibility()
        else:
            print("\n❌ 업그레이드 중 문제가 발생했습니다.")
    else:
        print("\n취소되었습니다.")
    
    print("\n프로그램을 종료하려면 Enter를 누르세요...")
    input()

if __name__ == "__main__":
    main()
