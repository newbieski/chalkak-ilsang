---
name: public-push-check
description: 공개 GitHub 저장소에 커밋·푸시하기 전에 비밀값·개인정보·비공개 자료·사진 EXIF를 점검한다. 푸시를 요청받았을 때, 또는 공개 저장소에 새 파일을 올리기 전에 사용한다.
---

# 공개 저장소 푸시 전 점검

공개 저장소는 한번 올라가면 삭제해도 기록이 남는다. 푸시 **전에** 아래를 순서대로 확인하고, 걸리는 게 있으면 사용자에게 보고한 뒤 결정을 받는다. 임의로 지우거나 임의로 그냥 올리지 않는다.

## 1. 무엇이 올라가는지부터 확정한다

```bash
git status --short
git diff --cached --stat
```

`git add -A` 나 `git add .` 로 뭉뚱그리지 말고 파일을 이름으로 지목해서 스테이징한다. 의도하지 않은 파일이 섞이는 사고 대부분이 여기서 난다.

## 2. 비밀값

```bash
git grep -nEi "(api[_-]?key|secret|password|passwd|token|credential|aws_access|aws_secret|bearer|private[_-]?key|BEGIN (RSA|OPENSSH))" -- $(git diff --cached --name-only)
```

`.env`, `credentials.json`, `*.pem`, `*.key`, `id_rsa` 같은 파일이 스테이징돼 있으면 무조건 멈추고 사용자에게 알린다. 파일명이 멀쩡해 보여도 내용을 열어 확인한다.

## 3. 개인정보

- 실명·이메일·전화번호·주민번호·집주소
- 실제 위치 좌표, 실제 계정 ID
- 대화 로그나 캡처에 남은 타인의 정보

테스트·더미 데이터라면 정말 가상의 값인지 확인한다. "샘플"이라고 적혀 있어도 실제 값을 복사해 온 경우가 있다.

## 4. 조직 내부·비공개 자료

공개해도 되는지 판단이 필요한 것들이라 특히 놓치기 쉽다.

- 수강생·직원 전용 자료의 **접근 URL이나 입장 코드** (경로에 코드가 박혀 있는 경우 포함)
- 과제 제출 폼, 사내 위키·이슈 트래커 주소
- 강의 자료나 사내 문서를 옮겨 적은 본문
- 사내 시스템 호스트명, 내부 IP

```bash
git grep -nE "https?://" -- $(git diff --cached --name-only)
```

URL은 전수로 훑어 하나씩 공개 가능 여부를 판단한다.

## 5. 이미지 EXIF

사진 파일이 포함될 때만. EXIF에 촬영 위치(GPS)와 기기 정보가 남아 있을 수 있다.

```powershell
Add-Type -AssemblyName System.Drawing
Get-ChildItem -Recurse -Include *.jpg,*.jpeg,*.tif,*.tiff | ForEach-Object {
    try {
        $img = [System.Drawing.Image]::FromFile($_.FullName)
        $ids = $img.PropertyIdList
        $gps = $ids | Where-Object { $_ -ge 1 -and $_ -le 31 }
        $make = $ids | Where-Object { $_ -eq 271 -or $_ -eq 272 }
        if ($gps -or $make) { "$($_.Name): GPS=$([bool]$gps) 기기정보=$([bool]$make)" }
        $img.Dispose()
    } catch { "$($_.Name): 읽기 실패 - 수동 확인 필요" }
}
```

걸리면 EXIF를 지우고 올릴지 사용자에게 묻는다. 위 방법이 안 되는 환경이면 자동 점검이 불가능하다고 솔직히 말하고 수동 확인을 요청한다.

## 6. 커밋 메타데이터

```bash
git config user.name
git config user.email
```

이 값은 커밋마다 공개 기록으로 남는다. 공개해도 되는 이메일인지 확인한다. 값이 비어 있거나 엉뚱하면(예: `a`) GitHub 계정에 커밋이 연결되지 않으니 사용자에게 알린다.

## 발견했을 때

사용자에게 **무엇이 · 어느 파일 몇 번째 줄에 · 왜 문제인지**를 짧게 보고하고 선택지를 준다. 보통 세 가지다.

1. 해당 부분만 제거하고 올린다
2. 파일 자체를 제외한다 (`.gitignore`)
3. 그대로 올린다

이미 커밋에 들어간 뒤에 발견했다면 히스토리에도 남는다는 점을 함께 알린다.

## 통과 후

점검 결과를 한 문단으로 요약해서 남기고 푸시한다. "무엇을 확인했고, 무엇을 고쳤고, 무엇은 사용자 판단으로 그대로 뒀는지"가 드러나야 한다.
