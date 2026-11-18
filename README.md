# BookStore Pro

Ứng dụng bán sách full-stack gồm **React + Vite** ở frontend và **FastAPI** ở backend. Frontend được viết bằng JSX và gọi API qua Vite proxy khi chạy ở môi trường phát triển.

## Công nghệ

| Phần | Công nghệ |
| --- | --- |
| Frontend | React 19, JSX, Vite |
| Backend | Python, FastAPI, SQLAlchemy |
| Cơ sở dữ liệu | PostgreSQL (Docker) hoặc SQLite để phát triển nhanh |
| Xác thực | JWT |

## Cấu trúc chính

```text
Eproject2/
├── backend/                 # FastAPI API, model và database
├── frontend/
│   ├── src/                 # Mã nguồn React (.jsx)
│   │   ├── views/           # Các màn hình người dùng và quản trị
│   │   ├── App.jsx          # Component gốc
│   │   └── main.jsx         # Điểm khởi động React
│   ├── static/              # Ảnh bìa và tài nguyên tĩnh
│   ├── package.json         # Lệnh npm của frontend
│   └── vite.config.js       # Vite + proxy API
├── docker-compose.yml       # PostgreSQL, API và frontend
├── .env.example             # Mẫu biến môi trường
└── run.py                   # Tiện ích chạy backend nhanh
```

## Chạy dự án bằng terminal (khuyên dùng khi phát triển)

Bạn cần mở **hai cửa sổ terminal** tại thư mục gốc dự án: một cho backend và một cho frontend.

### 1. Chuẩn bị backend

Tạo môi trường Python và cài thư viện (chỉ cần làm lần đầu):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Nếu PowerShell chặn lệnh kích hoạt môi trường ảo, chạy lệnh sau một lần trong cửa sổ hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Chạy backend

#### Cách nhanh nhất: SQLite, không cần Docker

Ở terminal thứ nhất, từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\Activate.ps1
python run.py --sqlite --no-browser
```

Backend sẽ chạy tại [http://127.0.0.1:8000](http://127.0.0.1:8000), tài liệu API ở [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

#### Dùng PostgreSQL qua Docker

Sao chép cấu hình mẫu nếu chưa có `.env`, sau đó thay `SECRET_KEY` bằng chuỗi ngẫu nhiên dài ít nhất 32 ký tự:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Mở terminal thứ nhất và chạy:

```powershell
.\.venv\Scripts\Activate.ps1
python run.py --no-browser
```

Lệnh này tự khởi động container PostgreSQL nếu Docker Desktop đang chạy, rồi chạy API ở cổng 8000.

### 3. Chạy frontend React (JSX)

Ở terminal thứ hai, từ thư mục gốc dự án:

```powershell
cd frontend
npm install
npm run dev
```

Mở đường dẫn Vite in ra trong terminal, mặc định là [http://localhost:5173](http://localhost:5173).

Trong lúc `npm run dev` còn chạy, mọi thay đổi trong file `.jsx` sẽ tự cập nhật trên trình duyệt. Vite chuyển các yêu cầu `/api` và `/health` sang backend tại `http://127.0.0.1:8000`, vì vậy backend phải đang chạy trước khi dùng các chức năng cần dữ liệu.

Nhấn `Ctrl + C` trong mỗi terminal để dừng dịch vụ tương ứng.

## Các lệnh frontend

Chạy các lệnh này trong thư mục `frontend`:

| Lệnh | Công dụng |
| --- | --- |
| `npm install` | Cài thư viện lần đầu hoặc sau khi thay đổi `package.json` |
| `npm run dev` | Chạy Vite development server tại cổng 5173 |
| `npm run build` | Tạo bản production vào `frontend/dist` |
| `npm run preview` | Xem thử bản production sau khi đã build |

## Chạy bản frontend đã build

Khi cần để FastAPI phục vụ bản React đã build, chạy:

```powershell
cd frontend
npm run build
cd ..
.\.venv\Scripts\Activate.ps1
python run.py --sqlite
```

Sau đó mở [http://127.0.0.1:8000](http://127.0.0.1:8000). FastAPI sẽ dùng thư mục `frontend/dist` nếu thư mục này tồn tại.

## Tài khoản demo

Database được nạp dữ liệu mẫu ở lần khởi động đầu tiên.

| Vai trò | Email | Mật khẩu |
| --- | --- | --- |
| Admin | `admin@bookstorepro.com` | `admin-password-123` |

## Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `npm` không được nhận diện | Cài Node.js bản LTS, đóng/mở lại terminal rồi chạy `node --version` và `npm --version`. |
| Web Vite không tải được dữ liệu | Kiểm tra terminal backend còn chạy tại cổng 8000. |
| Cổng 5173 đã được dùng | Dừng tiến trình đang dùng cổng đó hoặc chạy `npm run dev -- --port 5174`. |
| Không kết nối được PostgreSQL | Mở Docker Desktop, hoặc dùng `python run.py --sqlite`. |
| Trang 8000 chuyển sang `/legacy/` | Chạy `cd frontend; npm run build` để tạo `frontend/dist`, hoặc dùng Vite tại cổng 5173 khi phát triển. |

## Docker Compose

`docker compose up --build` hiện cần frontend image được build lại theo cấu trúc React/Vite. Trong lúc phát triển, cách chạy hai terminal ở trên là quy trình được hỗ trợ và cập nhật nhất.

## What to do now: just use 
 — the Docker stack is your running backend + frontend. Don't run uvicorn app.main:app again while Docker is up: Docker already owns port 8000, so a local uvicorn will hit the same WinError 10013, and the system Python 3.14 it defaults to lacks pgvector (the cause of the 500). If you ever need local --reload debugging, run it with the project venv on a free port instead

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001

## Check logs
docker compose logs -f api
docker compose logs -f frontend
## Restart
docker compose up -d --build
## Stop contain
docker compose down

## Special run
docker compose ps --format "{{.Name}} {{.Status}} {{.Ports}}" ; docker inspect bookstore-api --format "{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}"

docker inspect bookstore-api --format "{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}" ; $deadline = (Get-Date).AddSeconds(40); do { Start-Sleep -Seconds 2; $status = docker inspect bookstore-api --format "{{.State.Health.Status}}" } while ($status -ne "healthy" -and (Get-Date) -lt $deadline); Write-Output "health=$status"

curl.exe -sS -m 90 -X POST http://127.0.0.1:8000/api/v1/ai/chat -H "Content-Type: application/json" -H "X-Anonymous-ID: debug-d2ac4c" -d "{\"message\":\"Manga\"}"

curl.exe -sS -m 90 -X POST http://127.0.0.1:8000/api/v1/ai/chat -H 'Content-Type: application/json' -H 'X-Anonymous-ID: debug-d2ac4c' -d '{"message":"Manga"}'

Set-Content -Path "$env:TEMP\manga-chat.json" -Value '{"message":"Manga"}' -Encoding ascii; curl.exe -sS -m 90 -X POST http://127.0.0.1:8000/api/v1/ai/chat -H "Content-Type: application/json" -H "X-Anonymous-ID: debug-d2ac4c" --data-binary "@$env:TEMP\manga-chat.json"

docker logs bookstore-api --tail 80