    def run_validation_with_debug(self):
        """디버깅 강화된 검증 실행"""
        try:
            from validation_debugger import ValidationDebugger, enhanced_validation_with_debug, create_enhanced_annotated_pdf
            
            self.log("디버깅 모드로 검증을 시작합니다...")
            
            # 디버깅 강화 검증 실행
            validation_results, debug_results = enhanced_validation_with_debug(self.validator, self.filled_pdf_path)
            
            if not validation_results:
                self.log("검증 결과가 없습니다.")
                return
            
            # 결과 분석
            failed_count = len([r for r in validation_results if r.get('status') != 'OK'])
            total_count = len(validation_results)
            
            self.log(f"\n=== 검증 완료 ===")
            self.log(f"총 검증 항목: {total_count}개")
            self.log(f"실패 항목: {failed_count}개")
            self.log(f"성공률: {((total_count - failed_count) / total_count * 100):.1f}%")
            
            # 상세 결과 표시
            self.log(f"\n=== 상세 결과 ===")
            for result in validation_results:
                status_icon = "✅" if result.get('status') == 'OK' else "❌"
                self.log(f"{status_icon} {result['field_name']}: {result.get('message', '알 수 없음')}")
            
            # 디버깅 정보 표시
            if debug_results:
                self.log(f"\n=== 실패 원인 분석 ===")
                for debug_info in debug_results:
                    roi_name = debug_info['roi_name']
                    self.log(f"\n🔍 {roi_name} 분석:")
                    
                    if 'ssim_score' in debug_info:
                        self.log(f"  - 유사도(SSIM): {debug_info['ssim_score']:.4f}")
                        if debug_info['ssim_score'] > 0.995:
                            self.log(f"    ⚠️ 너무 유사함 (임계값 0.98로 조정 권장)")
                    
                    if 'text_difference' in debug_info:
                        self.log(f"  - 텍스트 차이: {debug_info['text_difference']}자")
                        self.log(f"  - 필요한 차이: {debug_info['threshold_required']}자 이상")
                        if debug_info['text_difference'] < debug_info['threshold_required']:
                            self.log(f"    💡 임계값을 {debug_info['text_difference']}로 낮춰보세요")
                    
                    if 'threshold_analysis' in debug_info:
                        self.log(f"  - Contour 분석:")
                        for thresh, data in debug_info['threshold_analysis'].items():
                            if data['total_area'] > 0:
                                self.log(f"    {thresh}: 면적 {data['total_area']}")
            
            # 강화된 주석 PDF 생성
            if failed_count > 0:
                output_dir = f"output/fail"
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_name = os.path.splitext(os.path.basename(self.filled_pdf_path))[0]
                output_path = f"{output_dir}/{pdf_name}_debug_{timestamp}.pdf"
                
                success = create_enhanced_annotated_pdf(
                    self.validator.original_pdf_path, 
                    self.filled_pdf_path, 
                    validation_results, 
                    debug_results, 
                    output_path
                )
                
                if success:
                    self.log(f"\n📁 강화된 디버깅 PDF 저장: {output_path}")
                    
                    # 디버깅 폴더 위치 안내
                    if debug_results:
                        debug_folder = debug_results[0].get('debug_session_dir', output_dir)
                        self.log(f"📊 상세 분석 파일: {debug_folder}")
            
            self.log("\n=== 검증 완료 ===")
            
        except Exception as e:
            self.log(f"디버깅 검증 실패: {str(e)}")
            messagebox.showerror("오류", f"디버깅 검증 실패:\n{str(e)}")
