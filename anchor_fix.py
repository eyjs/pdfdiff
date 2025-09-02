# 앵커 매칭 개선을 위한 임시 패치
# 이 코드를 pdf_validator_gui.py에서 _find_anchor_homography 함수를 교체하는 데 사용하세요

def _find_anchor_homography(self, page_img, anchor_img):
    """레거시 지원 - 새로운 강화 버전 호출"""
    print('[앵커 매칭] 강화된 다중 검출기 사용')
    return self._find_anchor_homography_robust(page_img, anchor_img)
