# PRD: 오늘 왜 떠? (Today's Hot Topic)

> **버전:** v1.0  
> **최종 수정일:** 2026-04-12  
> **상태:** Draft  

---

## 1. 제품 개요

| 항목 | 내용 |
|------|------|
| **제품명** | 오늘 왜 떠? (Today's Hot Topic) |
| **플랫폼** | 앱인토스 (App-in-Toss) 웹앱 |
| **한 줄 소개** | 커뮤니티의 자극적인 핫이슈를 AI로 요약하고 토스 포인트로 보상받는 도파민 허브 앱인토스 서비스 |

### 1.1 핵심 가치 제안

1. **정보 과잉 시대의 최적 포맷** — 가장 빠르고 자극적인 AI 3줄 요약 제공
2. **토스 리워드 루틴 활용** — 혜택 확인 습관을 활용한 자연스러운 리워드 경험
3. **네이티브 수준의 UX 신뢰도** — TDS(Toss Design System) 100% 준수

### 1.2 기술 스택

| 레이어 | 기술 | 선정 이유 |
|--------|------|-----------|
| **Frontend** | Next.js (App Router), Tailwind CSS, Framer Motion | 토스 특유의 부드러운 인터랙션 구현, SSR/SSG 지원 |
| **Backend** | FastAPI | AI 모델 연동 및 비동기 처리 최적화 |
| **Database** | PostgreSQL (Supabase) | 빠른 MVP 개발 및 실시간 투표 현황 반영 |
| **AI** | OpenAI GPT-4o | 커뮤니티 맥락 파악 및 자극적인 3줄 요약 생성 |
| **Infrastructure** | Toss App-in-Toss SDK | 로그인, 포인트 결제, mTLS 보안 통신 연동 |

---

## 2. 사용자 정의

### 2.1 주요 사용자: 리워드 헌터 (만보기/행운퀴즈 유저)

- **목표:** 최소한의 노력으로 최대한의 토스 포인트 적립
- **핵심 니즈:** 지루하지 않은 미션, 즉각적인 보상 확인

**유저 스토리:**

| ID | 스토리 | 이유 |
|----|--------|------|
| US-01 | 리워드 헌터로서, 나는 재미있는 썰을 읽으며 포인트를 얻고 싶다 | 단순 반복 미션은 지루하기 때문 |
| US-02 | 리워드 헌터로서, 나는 광고 시청 후 즉시 내 토스 포인트가 올라가는 것을 확인하고 싶다 | 보상의 효능감을 바로 느끼고 싶기 때문 |
| US-03 | 리워드 헌터로서, 나는 이슈에 투표하고 다른 사람들의 생각을 보고 싶다 | 내 선택이 다수와 일치하는지 궁금하기 때문 |

### 2.2 보조 사용자: 틈새 시간 킬링 유저

- **목표:** 송금/결제 후 남는 짧은 시간(1분 내외) 동안 트렌드 파악
- **핵심 니즈:** 로딩 없는 빠른 접속, 직관적인 요약 정보

**유저 스토리:**

| ID | 스토리 | 이유 |
|----|--------|------|
| US-04 | 틈새 시간 유저로서, 나는 지금 가장 핫한 커뮤니티 글을 3줄로 요약해서 보고 싶다 | 원문을 다 읽을 시간이 없기 때문 |
| US-05 | 틈새 시간 유저로서, 나는 토스 앱 안에서 나가지 않고 바로 정보를 소비하고 싶다 | 앱 전환이 번거롭기 때문 |
| US-06 | 틈새 시간 유저로서, 나는 내가 관심 있는 분야(주식, 연예 등)의 이슈만 골라보고 싶다 | 관심 없는 정보는 소음이기 때문 |

---

## 3. 핵심 기능 명세 (MVP)

### 3.1 TDS 기반 실시간 핫토픽 보드 `P0`

| 항목 | 내용 |
|------|------|
| **설명** | 커뮤니티(네이트판, 디시, 펨코 등) 크롤링 데이터를 카테고리별로 리스트화하여 노출 |
| **사용자 흐름** | 메인 홈 진입 → 카테고리 탭 선택 → 실시간 랭킹 리스트 확인 |
| **입력** | 카테고리 선택 (뉴스 / 썰 / 금융) |
| **출력** | 핫토픽 제목, 썸네일, 현재 실시간 순위, 조회수 |
| **비즈니스 규칙** | TDS 디자인 가이드라인 100% 준수하여 네이티브 앱처럼 보이게 함 |

**Acceptance Criteria:**
- [ ] 카테고리 탭 전환 시 리스트가 즉시 업데이트된다
- [ ] 각 토픽 아이템은 제목, 썸네일, 순위, 조회수를 표시한다
- [ ] TDS List Item 컴포넌트 스펙을 준수한다
- [ ] 스켈레톤 UI를 통해 로딩 상태를 표현한다

### 3.2 AI 3줄 요약 및 과몰입 투표 엔진 `P0`

| 항목 | 내용 |
|------|------|
| **설명** | GPT-4o를 이용해 게시글 요약 및 찬반/선호도 투표 생성 |
| **사용자 흐름** | 리스트 클릭 → 요약본 열람 → 하단 투표 버튼 클릭 → 결과 확인 및 보상 트리거 |
| **입력** | 투표 선택값 (Option A / Option B) |
| **출력** | 요약 텍스트 3줄, 투표 퍼센티지 현황 |
| **비즈니스 규칙** | AI 가드레일을 통해 혐오 표현 필터링, 투표 참여는 1인 1회 제한 |

**Acceptance Criteria:**
- [ ] AI 요약은 정확히 3줄로 제공된다
- [ ] 혐오 표현이 포함된 요약은 자동 필터링된다
- [ ] 유저당 투표는 토픽별 1회로 제한된다
- [ ] 투표 후 실시간 퍼센티지가 애니메이션과 함께 표시된다
- [ ] 투표 완료 시 포인트 보상 트리거가 발동한다

### 3.3 mTLS 기반 토스 포인트 지급 모듈 `P0`

| 항목 | 내용 |
|------|------|
| **설명** | 투표 완료 또는 광고 시청 후 유저에게 실제 토스 포인트 지급 |
| **사용자 흐름** | 투표 완료 → '포인트 받기' 팝업 노출 → 클릭 시 토스 포인트 잔액 업데이트 |
| **입력** | 유저 식별자, 보상 ID |
| **출력** | 지급 성공 여부, 현재 잔액 |
| **비즈니스 규칙** | 반드시 mTLS 통신을 사용하며, 일일 최대 지급 한도 설정 |

**Acceptance Criteria:**
- [ ] mTLS 인증서 기반 보안 통신이 적용된다
- [ ] 포인트 지급 성공 시 잔액이 즉시 업데이트된다
- [ ] 일일 지급 한도 초과 시 안내 메시지를 표시한다
- [ ] 지급 실패 시 재시도 로직이 동작한다
- [ ] 포인트 지급 애니메이션이 표시된다

---

## 4. 페이지 목록 및 화면 구조

### 4.1 홈 페이지 (Home) — `/`

```
┌─────────────────────────────┐
│  [뉴스]  [썰]  [금융]       │  ← 카테고리 탭 (Sticky)
├─────────────────────────────┤
│  🔥 1. 핫토픽 제목 A        │
│     조회 12.3만 · 2시간 전   │
├─────────────────────────────┤
│  🔥 2. 핫토픽 제목 B        │
│     조회 9.8만 · 3시간 전    │
├─────────────────────────────┤
│  ...                        │
└─────────────────────────────┘
```

- 상단 카테고리 탭: 뉴스 / 썰 / 금융
- 실시간 핫토픽 리스트 (TDS List Item 컴포넌트)
- Pull-to-refresh 지원

### 4.2 상세 페이지 (Detail) — `/topics/{id}`

```
┌─────────────────────────────┐
│  ← 뒤로가기         공유 ↗  │
├─────────────────────────────┤
│  이슈 제목                   │
│  출처: 네이트판 · 3시간 전    │
├─────────────────────────────┤
│  ┌─ AI 3줄 요약 ──────────┐ │
│  │ 1. 첫 번째 요약 문장     │ │
│  │ 2. 두 번째 요약 문장     │ │
│  │ 3. 세 번째 요약 문장     │ │
│  └─────────────────────────┘ │
├─────────────────────────────┤
│  [관련 이미지]               │
├─────────────────────────────┤
│  너의 생각은?                │
│  ┌──────┐    ┌──────┐       │
│  │  A안  │    │  B안  │      │
│  └──────┘    └──────┘       │
├─────────────────────────────┤
│  투표 결과: A 62% / B 38%   │
│  참여자 1,234명              │
└─────────────────────────────┘
```

- 이슈 제목 및 출처 정보
- AI 3줄 요약 카드 (강조 카드 UI)
- 관련 이미지 영역
- 찬/반 투표 섹션 및 실시간 결과 표시

### 4.3 보상 완료 팝업 (Reward Modal)

```
┌─────────────────────────────┐
│                             │
│      🎉 +10 포인트!         │
│                             │
│   투표 참여 보상이           │
│   지급되었어요               │
│                             │
│   현재 잔액: 1,230P         │
│                             │
│  [친구에게 공유하기]         │
│  [확인]                     │
└─────────────────────────────┘
```

- 포인트 지급 애니메이션 (Framer Motion)
- 현재 잔액 표시
- '친구에게 공유' 버튼

### 4.4 마이 페이지 (Profile) — `/profile`

```
┌─────────────────────────────┐
│  내 정보                     │
├─────────────────────────────┤
│  총 적립 포인트: 1,230P      │
├─────────────────────────────┤
│  도파민 패스: 미가입          │
│  [구독하기]                  │
├─────────────────────────────┤
│  포인트 내역                 │
│  · +10P  투표 참여  4/12     │
│  · +20P  광고 시청  4/12     │
│  · +10P  투표 참여  4/11     │
├─────────────────────────────┤
│  알림 설정                   │
│  핫토픽 알림  [ON/OFF]       │
└─────────────────────────────┘
```

- 내 포인트 내역 리스트
- 도파민 패스(구독) 가입 상태 및 CTA
- 알림 설정 토글

---

## 5. 데이터 모델

### 5.1 ERD

```
User ──< VoteLog >── Poll ──── Topic
  │                              
  └──< PointTransaction          
```

### 5.2 테이블 정의

#### User
| 컬럼 | 타입 | 설명 | 제약조건 |
|------|------|------|----------|
| `id` | UUID | PK | NOT NULL |
| `toss_user_id` | VARCHAR | 토스 유저 고유 ID | UNIQUE, NOT NULL |
| `is_premium` | BOOLEAN | 도파민 패스 구독 여부 | DEFAULT false |
| `total_points` | INTEGER | 누적 포인트 | DEFAULT 0 |
| `created_at` | TIMESTAMP | 가입일시 | DEFAULT now() |

#### Topic
| 컬럼 | 타입 | 설명 | 제약조건 |
|------|------|------|----------|
| `id` | UUID | PK | NOT NULL |
| `title` | VARCHAR(200) | 토픽 제목 | NOT NULL |
| `source_url` | TEXT | 원문 URL | NOT NULL |
| `category` | VARCHAR(20) | 카테고리 (news/story/finance) | NOT NULL |
| `summary_json` | JSONB | AI 요약 데이터 (3줄) | — |
| `image_url` | TEXT | 대표 이미지 URL | — |
| `view_count` | INTEGER | 조회수 | DEFAULT 0 |
| `created_at` | TIMESTAMP | 생성일시 | DEFAULT now() |

#### Poll
| 컬럼 | 타입 | 설명 | 제약조건 |
|------|------|------|----------|
| `id` | UUID | PK | NOT NULL |
| `topic_id` | UUID | FK → Topic.id | NOT NULL |
| `option_a_text` | VARCHAR(100) | 선택지 A 텍스트 | NOT NULL |
| `option_b_text` | VARCHAR(100) | 선택지 B 텍스트 | NOT NULL |
| `option_a_count` | INTEGER | A 투표수 | DEFAULT 0 |
| `option_b_count` | INTEGER | B 투표수 | DEFAULT 0 |

#### VoteLog
| 컬럼 | 타입 | 설명 | 제약조건 |
|------|------|------|----------|
| `id` | UUID | PK | NOT NULL |
| `user_id` | UUID | FK → User.id | NOT NULL |
| `poll_id` | UUID | FK → Poll.id | NOT NULL |
| `selected_option` | VARCHAR(1) | 선택한 옵션 (A/B) | NOT NULL |
| `created_at` | TIMESTAMP | 투표일시 | DEFAULT now() |

> **UNIQUE 제약:** `(user_id, poll_id)` — 유저당 투표 1회 제한

#### PointTransaction
| 컬럼 | 타입 | 설명 | 제약조건 |
|------|------|------|----------|
| `id` | UUID | PK | NOT NULL |
| `user_id` | UUID | FK → User.id | NOT NULL |
| `amount` | INTEGER | 지급/차감 포인트 | NOT NULL |
| `reason` | VARCHAR(50) | 지급 사유 (vote/ad/share) | NOT NULL |
| `status` | VARCHAR(20) | 상태 (pending/success/failed) | DEFAULT 'pending' |
| `created_at` | TIMESTAMP | 생성일시 | DEFAULT now() |

---

## 6. API 설계

### 6.1 엔드포인트 목록

#### `GET /api/v1/topics`
카테고리별 핫토픽 리스트 조회

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `category` | query string | N | `news` / `story` / `finance` (기본값: 전체) |
| `page` | query string | N | 페이지 번호 (기본값: 1) |
| `limit` | query string | N | 페이지당 항목 수 (기본값: 20) |

**Response (200):**
```json
{
  "topics": [
    {
      "id": "uuid",
      "title": "핫토픽 제목",
      "category": "story",
      "image_url": "https://...",
      "view_count": 12300,
      "rank": 1,
      "created_at": "2026-04-12T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

---

#### `GET /api/v1/topics/{id}`
특정 토픽 상세 및 AI 요약 정보 조회

**Response (200):**
```json
{
  "id": "uuid",
  "title": "핫토픽 제목",
  "source_url": "https://...",
  "category": "story",
  "summary": [
    "첫 번째 요약 문장입니다.",
    "두 번째 요약 문장입니다.",
    "세 번째 요약 문장입니다."
  ],
  "image_url": "https://...",
  "view_count": 12300,
  "poll": {
    "id": "uuid",
    "option_a_text": "찬성",
    "option_b_text": "반대",
    "option_a_count": 620,
    "option_b_count": 380,
    "user_voted": null
  },
  "created_at": "2026-04-12T10:00:00Z"
}
```

---

#### `POST /api/v1/polls/{id}/vote`
투표 참여 및 실시간 결과 반환

**Request Body:**
```json
{
  "selected_option": "A"
}
```

**Response (200):**
```json
{
  "poll_id": "uuid",
  "selected_option": "A",
  "option_a_count": 621,
  "option_b_count": 380,
  "reward_eligible": true
}
```

**Error (409 — 중복 투표):**
```json
{
  "error": "ALREADY_VOTED",
  "message": "이미 투표에 참여하셨습니다."
}
```

---

#### `POST /api/v1/rewards/claim`
포인트 지급 요청 (Toss API 연동)

**Request Body:**
```json
{
  "reward_type": "vote",
  "reference_id": "uuid"
}
```

**Response (200):**
```json
{
  "transaction_id": "uuid",
  "amount": 10,
  "status": "success",
  "current_balance": 1230
}
```

**Error (429 — 일일 한도 초과):**
```json
{
  "error": "DAILY_LIMIT_EXCEEDED",
  "message": "오늘의 포인트 지급 한도에 도달했습니다."
}
```

---

#### `GET /api/v1/users/me`
현재 유저 정보 및 포인트 확인

**Response (200):**
```json
{
  "id": "uuid",
  "toss_user_id": "toss_12345",
  "is_premium": false,
  "total_points": 1230,
  "today_earned": 40,
  "created_at": "2026-04-01T00:00:00Z"
}
```

---

## 7. 인증 및 권한

### 7.1 인증 방식

- **앱인토스 SDK 자동 로그인:** Toss Access Token을 활용한 SSO
- 토스 앱 내부에서 서비스 진입 시 자동으로 인증 토큰 전달
- 모든 API 요청 헤더에 `Authorization: Bearer {toss_access_token}` 포함

### 7.2 권한 레벨

| 구분 | 일반 유저 | 프리미엄 (도파민 패스) |
|------|-----------|----------------------|
| AI 요약본 열람 | O | O |
| 투표 참여 | O | O |
| 일반 보상 | O | O (2배) |
| 광고 노출 | O | X (광고 제거) |
| 무삭제 풀버전 접근 | X | O |

---

## 8. 프로젝트 구조

```
src/
├── app/                    # Next.js App Router (Pages & Layouts)
│   ├── layout.tsx          # 루트 레이아웃 (TDS 전역 스타일)
│   ├── page.tsx            # 홈 페이지
│   ├── topics/
│   │   └── [id]/
│   │       └── page.tsx    # 토픽 상세 페이지
│   └── profile/
│       └── page.tsx        # 마이 페이지
├── components/
│   ├── common/             # TDS 기반 공통 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── ListItem.tsx
│   │   ├── Modal.tsx
│   │   └── Skeleton.tsx
│   ├── home/               # 홈 화면 전용 컴포넌트
│   │   ├── CategoryTabs.tsx
│   │   └── TopicList.tsx
│   └── topic/              # 요약 및 투표 섹션 컴포넌트
│       ├── SummaryCard.tsx
│       ├── PollSection.tsx
│       └── RewardModal.tsx
├── lib/
│   ├── toss/               # Toss SDK 및 mTLS 통신 로직
│   │   ├── auth.ts
│   │   ├── points.ts
│   │   └── mtls.ts
│   ├── openai/             # GPT-4o 프롬프트 및 API 연동
│   │   ├── client.ts
│   │   └── prompts.ts
│   └── supabase/           # DB Client 설정
│       └── client.ts
├── hooks/                  # 커스텀 훅
│   ├── useAuth.ts
│   ├── useTopics.ts
│   └── useVote.ts
├── services/               # 비즈니스 로직
│   ├── pointService.ts
│   ├── voteService.ts
│   └── topicService.ts
└── types/                  # TypeScript 타입 정의
    ├── topic.ts
    ├── user.ts
    └── poll.ts
```

---

## 9. 환경변수 및 외부 서비스

### 9.1 환경변수

| 변수명 | 용도 | 비고 |
|--------|------|------|
| `OPENAI_API_KEY` | GPT-4o 연동용 | 서버 사이드 전용 |
| `TOSS_CLIENT_ID` | 토스 인증 API | — |
| `TOSS_CLIENT_SECRET` | 토스 인증 API | 서버 사이드 전용 |
| `TOSS_MTLS_CERT` | mTLS 보안 인증서 경로 | 서버 사이드 전용 |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | 클라이언트 노출 가능 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 익명 키 | 클라이언트 노출 가능 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 롤 키 | 서버 사이드 전용 |

### 9.2 외부 서비스

| 서비스 | 용도 | 연동 방식 |
|--------|------|-----------|
| **Toss App-in-Toss SDK** | 인증, 포인트 지급 | SDK + mTLS REST API |
| **OpenAI API** | 커뮤니티 글 3줄 요약 생성 | REST API (GPT-4o) |
| **Supabase** | DB, 실시간 구독 | PostgreSQL + Realtime |

---

## 10. 개발 태스크

### P0 — MVP 필수 (1차 릴리즈)

- [ ] Toss SDK 연동 및 유저 자동 로그인 구현
- [ ] 커뮤니티 데이터 크롤링 및 GPT-4o 요약 파이프라인 구축
- [ ] TDS 준수 메인 리스트 UI 개발 (홈 페이지)
- [ ] 토픽 상세 페이지 UI 개발 (AI 요약 카드 + 투표)
- [ ] 투표 기능 구현 (1인 1회 제한, 실시간 결과 반영)
- [ ] 토스 포인트 지급 API 연동 (mTLS 보안 통신)
- [ ] 보상 완료 팝업 모달 개발

### P1 — 확장 기능 (2차 릴리즈)

- [ ] 보상형 동영상 광고(IAA) 레이아웃 및 트리거 구현
- [ ] 토스페이 정기결제 연동 (도파민 패스 구독)
- [ ] 카테고리별 필터링 및 검색 기능
- [ ] 마이 페이지 (포인트 내역, 구독 관리)

### P2 — 성장 기능 (3차 릴리즈)

- [ ] 투표 데이터 통계 시각화 대시보드 (B2B용)
- [ ] 친구 공유 시 추가 포인트 지급 바이럴 루프 구현
- [ ] 이슈 발생 시 토스 푸시 알림 API 연동
