# Tab Motion 3D

갤럭시 탭 S10 FE+용 첫 구현: 전면 카메라의 전신 자세를 MediaPipe Pose Lite로 기기 안에서 읽고, 움직이는 3D 관절 캐릭터를 OpenGL ES로 표시합니다. 영상은 외부 서버로 전송하지 않습니다.

이 버전은 Kalidoface의 VRM 캐릭터나 얼굴 표정·손가락 추적을 포함하지 않습니다. 저지연 전신 추적을 검증하는 첫 단계입니다. 프레임 수치는 기기에서 측정해야 합니다.

## APK 만들기

GitHub 새 저장소에 이 폴더의 내용을 올린 뒤 Actions > Build debug APK > Run workflow를 누르고 완료된 실행의 `TabMotion3D-debug-apk` 아티팩트를 받습니다. ZIP을 풀어 `app-debug.apk`를 태블릿에 설치합니다. Android Studio에서도 Gradle Sync 후 실행 가능합니다. 빌드 중 공식 Pose Lite 모델이 내려받아져 APK에 포함되므로 설치 뒤 인터넷이 필요 없습니다.

## 설계

- 640×480 카메라 분석, 최신 프레임만 유지, 약 30Hz 인식 상한, 60fps 화면 요청.
- 배경 분리 없음, 1명 추적, 결과 사이에 부드러운 보간.
- 기기 GPU delegate를 우선 시도하고 초기화에 실패하면 CPU로 전환.
- 한 번에 1개 이미지만 추론하고 인식 결과를 그리는 스레드에 안전하게 전달.

이 환경에는 Android SDK가 없어 APK 컴파일 및 실제 탭 S10 FE+ 성능 측정은 완료하지 못했습니다.
