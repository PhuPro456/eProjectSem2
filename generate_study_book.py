from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Save to updated file and attempt overwrite if unlocked
OUT_UPDATED = Path('Sach_hoc_va_thuyet_trinh_BookStore_Pro_Updated.docx')
OUT_ORIGINAL = Path('Sach_hoc_va_thuyet_trinh_BookStore_Pro.docx')

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)

def borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{edge}')
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), '4')
        e.set(qn('w:color'), 'D0D7DE')
        b.append(e)
    tblPr.append(b)

def set_cell(cell, text, bold=False, color=None, font_size=9, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = 'Aptos'
    r.font.size = Pt(font_size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.7)
sec.bottom_margin = Inches(0.7)
sec.left_margin = Inches(0.75)
sec.right_margin = Inches(0.75)

styles = doc.styles
styles['Normal'].font.name = 'Aptos'
styles['Normal']._element.rPr.rFonts.set(qn('w:ascii'), 'Aptos')
styles['Normal']._element.rPr.rFonts.set(qn('w:hAnsi'), 'Aptos')
styles['Normal'].font.size = Pt(10)
styles['Normal'].paragraph_format.line_spacing = 1.15

for n, size, color in [('Title', 23, '0F2D24'), ('Heading 1', 14.5, '154734'), ('Heading 2', 12, '1E5A44'), ('Heading 3', 10.5, '2A6F54')]:
    s = styles[n]
    s.font.name = 'Aptos Display'
    s.font.size = Pt(size)
    s.font.bold = True
    s.font.color.rgb = RGBColor.from_string(color)

def title(text, subtitle=None):
    p = doc.add_paragraph(style='Title')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(text)
    if subtitle:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p2.add_run(subtitle)
        r.italic = True
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(90, 90, 90)
    doc.add_paragraph()

def h(text, level=1):
    x = doc.add_heading(text, level=level)
    x.paragraph_format.space_before = Pt(9)
    x.paragraph_format.space_after = Pt(3)
    return x

def p(text='', boldlead=None):
    x = doc.add_paragraph()
    x.paragraph_format.space_after = Pt(4)
    if boldlead:
        r = x.add_run(boldlead)
        r.bold = True
    x.add_run(text)
    return x

def bullet(text, level=0):
    x = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    x.paragraph_format.space_after = Pt(2)
    x.add_run(text)
    return x

def code(text):
    x = doc.add_paragraph()
    x.paragraph_format.left_indent = Inches(0.2)
    x.paragraph_format.space_before = Pt(2)
    x.paragraph_format.space_after = Pt(4)
    r = x.add_run(text)
    r.font.name = 'Consolas'
    r._element.rPr.rFonts.set(qn('w:ascii'), 'Consolas')
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(30, 70, 50)
    return x

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    borders(t)
    for i, x in enumerate(headers):
        shade(t.rows[0].cells[i], '154734')
        set_cell(t.rows[0].cells[i], x, True, 'FFFFFF', 9)
    for n, row in enumerate(rows):
        cells = t.add_row().cells
        bg = 'F8FAF9' if n % 2 == 1 else 'FFFFFF'
        for i, x in enumerate(row):
            shade(cells[i], bg)
            set_cell(cells[i], str(x), font_size=8.5)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t

# ----------------- NỘI DUNG SÁCH HỌC VÀ THUYẾT TRÌNH -----------------

title('Sách học và thuyết trình BookStore Pro', 'Tài liệu ôn tập kiến trúc Fullstack React 19 + FastAPI + AI cho bảo vệ đồ án CNTT FPT-Aptech')

p('Tài liệu này được biên soạn bám sát 100% source code thực tế của dự án BookStore Pro. Cuốn sách giúp bạn hiểu sâu sắc kiến trúc tách rời (Decoupled Architecture), nắm vững đường đi của dữ liệu từ Frontend React Component qua REST API FastAPI, xuống SQLAlchemy ORM, Database PostgreSQL, tầng AI Hybrid (NLP Lexicon & LLM Gemini), cùng toàn bộ quy trình đóng gói Docker container.')

h('Cách dùng cuốn sách để ôn thi hiệu quả', 1)
table(['Mục tiêu ôn tập', 'Chương cần đọc kỹ', 'Kỹ năng cần đạt được'], [
    ['Ôn nhanh 30 phút trước giờ bảo vệ', 'Chương 1, 2, 10, 11, 12', 'Nắm vững cốt truyện demo, trả lời gãy gọn 10 câu hỏi phản biện cốt lõi.'],
    ['Bị hỏi chuyên sâu Frontend', 'Chương 7', 'Giải thích kiến trúc React 19 SPA, Hash Router, Global Store Observer (useSyncExternalStore), API Client, Form debounce, Modal & Cart Drawer.'],
    ['Bị hỏi chuyên sâu Backend & DB', 'Chương 3, 4, 5', 'Giải thích Lifespan, Depends injection, Pydantic contract, SQLAlchemy CheckConstraint, Transaction khóa hàng (with_for_update).'],
    ['Bị hỏi về AI & Xử lý ngôn ngữ', 'Chương 6', 'Giải thích cơ chế AI Hybrid: Local NLP Lexicon Sentiment, Rule-based Chat & Khuyến nghị, cùng cơ chế mã hóa Fernet bảo vệ Gemini API Key.'],
    ['Bị hỏi về DevOps & Triển khai', 'Chương 8', 'Giải thích Dockerfile multi-stage, Docker Compose 3 service (postgres, api, frontend nginx), Nginx reverse proxy, Health check dependency.']
], [2.0, 1.8, 3.2])

h('Mục lục toàn diện', 1)
for x in [
    '1. Bức tranh tổng thể hệ thống Fullstack',
    '2. Các luồng nghiệp vụ xương sống (Must-Know Flows)',
    '3. Backend: Khởi tạo, Cấu hình và Điểm vào FastAPI',
    '4. Cơ sở dữ liệu, Model ORM và Tầng CRUD',
    '5. Đặc tả API, Xác thực JWT và Phân quyền RBAC',
    '6. Phân hệ AI: Phân tích cảm xúc, Khuyến nghị & Kết nối LLM Gemini',
    '7. Frontend: Kiến trúc React 19 SPA, State Management & Views',
    '8. Đóng gói Container, Vận hành Docker và Mở rộng Kubernetes/Power BI',
    '9. Bản đồ giải thích toàn bộ tệp tin trong Repository',
    '10. Kịch bản thuyết trình Live Demo 8-10 phút gây ấn tượng hội đồng',
    '11. Bộ 20 câu hỏi phản biện thường gặp và Đáp án chuẩn xác',
    '12. Phiếu ôn tập nhanh 15 phút trước khi bước vào phòng thi'
]:
    bullet(x)

# CHƯƠNG 1
h('1. Bức tranh tổng thể hệ thống Fullstack', 1)
p('BookStore Pro là giải pháp thương mại điện tử chuyên ngành sách CNTT, được kiến trúc theo chuẩn Single Page Application (SPA) tách rời hoàn toàn với Backend RESTful API.')
code('Trình duyệt (React 19 SPA)  <--->  Nginx Reverse Proxy / Vite  <--->  FastAPI Backend (/api/v1)  <--->  PostgreSQL 16')
p('Lợi ích kỹ thuật của kiến trúc này:')
bullet('Độc lập môi trường: Đội ngũ Frontend và Backend có thể phát triển song song. Frontend build thành tĩnh (Static bundle HTML/CSS/JS) đưa vào Nginx; Backend đóng gói image Python gọn nhẹ.')
bullet('Bảo mật dữ liệu tuyệt đối: Không bao giờ tin tưởng dữ liệu từ Client. Mọi kiểm tra quyền, số lượng tồn kho, giá bán và tổng tiền đều do Backend và Database Engine bảo vệ qua Transaction.')
bullet('Hiệu năng tối ưu: Frontend tải một lần duy nhất, chuyển trang không giật lag. Backend hỗ trợ cả router đồng bộ lẫn bất đồng bộ (books_async.py) cho các truy vấn dữ liệu lớn.')

table(['Thành phần', 'Công nghệ & Thư viện', 'Trách nhiệm chính', 'Điều tối kỵ (Không làm ở đây)'], [
    ['Frontend', 'React 19, Vite, Vanilla CSS', 'Render UI, nhận tương tác, lưu giỏ hàng tạm, bắt lỗi form, gọi API.', 'Không tính toán tổng tiền thanh toán cuối cùng; không tin nút ẩn/hiện để phân quyền.'],
    ['API Gateway / Router', 'FastAPI, APIRouter, OAuth2 Bearer', 'Nhận HTTP request, decode JWT, kiểm tra Role RBAC, map Schema Pydantic.', 'Không viết câu lệnh SQL phức tạp hay logic nghiệp vụ trừ kho trực tiếp trong router.'],
    ['Business & CRUD Service', 'SQLAlchemy 2.0 ORM, Python Service', 'Thực thi nghiệp vụ, quản lý Transaction, khóa hàng tồn kho, tính cảm xúc NLP.', 'Không truy cập trực tiếp vào đối tượng HTTP Request/Response.'],
    ['Database Storage', 'PostgreSQL 16 / SQLite', 'Lưu trữ bền vững, ép buộc ràng buộc toàn vẹn (CheckConstraint, Foreign Key, Index).', 'Không trả dữ liệu thô ra môi trường Internet mà chưa qua Pydantic schema serialization.'],
    ['AI Engine', 'NLP Lexicon + Gemini 3.5 Flash', 'Phân tích sentiment nhận xét, tư vấn sách theo chủ đề/ngân sách, trò chuyện tự nhiên.', 'Không để AI tự bịa giá, tồn kho hoặc tự truy cập vào dữ liệu người dùng khác.']
], [1.3, 1.8, 2.4, 1.5])

# CHƯƠNG 2
h('2. Các luồng nghiệp vụ xương sống (Must-Know Flows)', 1)
h('Luồng 1: Tìm kiếm, Lọc danh mục và Xem chi tiết sách', 2)
code('User nhập ô tìm kiếm / chọn thể loại -> CatalogView.jsx (debounce 260ms) -> api.listBooks() -> GET /api/v1/books?query=...&category=... -> crud.build_books_query() -> SELECT books WHERE ... -> Pydantic PaginatedBooks -> React render BookCard')
p('Điểm kỹ thuật mấu chốt để ghi điểm:', 'Kỹ thuật: ')
bullet('Frontend áp dụng kỹ thuật Debounce 260ms: Giúp người dùng gõ phím liên tục mà không làm ngập (flood) server bằng hàng chục request thừa.')
bullet('Backend lọc trực tiếp trên PostgreSQL Index: Kết hợp LIKE %query% trên cột title/author và category_code; tính toán tổng số bản ghi (total) để trả về cho Frontend vẽ phân trang chuẩn xác.')

h('Luồng 2: Đăng nhập và Cơ chế Bảo mật JWT Stateless', 2)
code('User điền email & mật khẩu -> AuthView.jsx -> api.login() -> POST /api/v1/auth/login -> verify_password(pwd, hash) qua Argon2 -> create_access_token(sub=user.id, role=user.role) -> Trả JWT token -> store.setToken() -> Lưu LocalStorage')
p('Cách trả lời khi hội đồng hỏi về luồng Auth:', 'Cơ chế: ')
bullet('Mật khẩu của người dùng được mã hóa bằng thuật toán Argon2 (thư viện pwdlib). Mật khẩu gốc không bao giờ được ghi lại ở bất kỳ đâu.')
bullet('Mỗi request bảo mật từ Frontend gửi kèm header: Authorization: Bearer <token>.')
bullet('Tại Backend, hàm dependency get_current_user giải mã token, xác thực chữ ký số bằng SECRET_KEY và nạp User model từ database. Nếu là endpoint quản trị (/api/v1/admin/...), dependency get_current_admin sẽ kiểm tra if user.role != "admin" thì trả ngay mã lỗi HTTP 403 Forbidden.')

h('Luồng 3: Giỏ hàng, Đặt hàng và Giao dịch Khóa dòng (Concurrency Transaction)', 2)
code('User bấm Thêm giỏ hàng -> store.cartAdd() (Local State) -> Mở Cart Drawer -> Bấm Checkout -> api.createOrder() -> POST /api/v1/orders -> crud/order.py: create_order() -> WITH_FOR_UPDATE khóa dòng sách -> Kiểm tra stock -> Tạo Order + OrderItem -> Trừ stock -> db.commit() -> Trả về OrderRead -> store.cartClear()')
p('Điểm kỹ thuật cao cấp nhất dự án (Bắt buộc phải nói):', 'Điểm sáng: ')
bullet('Xử lý tranh chấp đồng thời (Race Condition): Nếu 2 khách hàng cùng đặt cuốn sách cuối cùng trong kho tại cùng một mili-giây, hàm crud.create_order sử dụng truy vấn: db.execute(select(Book).filter(...).with_for_update()). Database PostgreSQL sẽ lập tức khóa (Row-level lock) các dòng sách đó. Giao dịch đầu tiên trừ tồn kho thành công; giao dịch thứ hai đọc lại thấy tồn kho bằng 0 sẽ bị từ chối với lỗi HTTP 400 "Not enough stock" an toàn, không bao giờ bị âm kho.')
bullet('Snapshot giá lịch sử: Bảng order_items sao chép lại chính xác title và unit_price ngay lúc mua. Nhờ vậy, ngay cả khi Admin chỉnh sửa giá cuốn sách sau đó, hóa đơn cũ của khách hàng vẫn giữ nguyên giá trị lịch sử.')

h('Luồng 4: Đánh giá sách và Động cơ Phân tích Cảm xúc (NLP Sentiment)', 2)
code('User gửi đánh giá 5 sao + nhận xét -> POST /api/v1/books/{id}/reviews -> analyze_sentiment(text, rating) -> Trích xuất keywords + gán nhãn positive/neutral/negative -> Lưu bảng reviews -> Admin Reviews Dashboard hiển thị biểu đồ')
p('sentiment.py xử lý từ vựng kết hợp: nhận diện các từ tích cực (tuyệt vời, hay, xuất sắc), từ tiêu cực (tệ, chán, lỗi), xử lý phủ định (không hay, chẳng đáng) và nhân hệ số trọng số từ ngữ nhấn mạnh. Đây là mô hình Heuristic minh bạch, chạy offline tốc độ cực cao.')

# CHƯƠNG 3
h('3. Backend: Khởi tạo, Cấu hình và Điểm vào FastAPI', 1)
table(['Tệp tin', 'Vị trí trong mã nguồn', 'Nhiệm vụ & Điểm nhấn kỹ thuật'], [
    ['backend/app/main.py', 'Điểm vào của ứng dụng FastAPI', 'Sử dụng lifespan context manager để khởi tạo cơ sở dữ liệu và seed dữ liệu mẫu tự động; đăng ký api_router tại tiền tố /api/v1; cung cấp endpoint /health; tự động mount build tĩnh của React Frontend (frontend/dist) khi chạy local.'],
    ['backend/app/core/config.py', 'Quản lý cấu hình tập trung', 'Đọc tệp môi trường .env; bắt buộc khai báo DATABASE_URL và SECRET_KEY (tối thiểu 32 ký tự); sử dụng @lru_cache để chỉ khởi tạo đối tượng cấu hình một lần duy nhất.'],
    ['backend/app/db/session.py', 'Quản lý kết nối Database Sync', 'Tạo engine SQLAlchemy và SessionLocal. Thiết lập pool_pre_ping=True để tự động phục hồi kết nối database bị ngắt; cung cấp dependency get_db cho FastAPI.'],
    ['backend/app/db/session_async.py', 'Kết nối Database Bất đồng bộ', 'Sử dụng create_async_engine và AsyncSession phục vụ riêng cho các endpoint /books-async nhằm đối chiếu hiệu năng truy vấn song song.'],
    ['backend/app/api/deps.py', 'Tầng bảo vệ và Dependency Injection', 'Cung cấp các dependency: DatabaseSession, get_current_user, get_optional_user, get_current_admin. Xử lý giải mã JWT và kiểm tra cờ is_active của người dùng.']
], [2.2, 2.0, 2.8])

# CHƯƠNG 4
h('4. Cơ sở dữ liệu, Model ORM và Tầng CRUD', 1)
p('Toàn bộ hệ thống cơ sở dữ liệu được định nghĩa bằng SQLAlchemy 2.0 cú pháp mới với kiểu dữ liệu Mapped và mapped_column:')
table(['Bảng dữ liệu', 'Model Class', 'Các trường và Ràng buộc toàn vẹn quan trọng'], [
    ['users', 'User (models/user.py)', 'id (PK), name, email (Unique), hashed_password, role (CheckConstraint: customer hoặc admin), is_active, created_at.'],
    ['categories', 'Category (models/book.py)', 'code (PK, VARCHAR 50), name (Unique, VARCHAR 100).'],
    ['books', 'Book (models/book.py)', 'id (PK), title, author, category_code (FK categories.code với ON DELETE RESTRICT), price (Numeric 10,2), stock (Integer), cover (URL). CheckConstraint: price >= 0 và stock >= 0.'],
    ['orders', 'Order (models/order.py)', 'id (PK), user_id (FK users.id CASCADE), status (CheckConstraint: pending, paid, shipped, completed, cancelled), total (Numeric 12,2), created_at. Quan hệ items với cascade all, delete-orphan.'],
    ['order_items', 'OrderItem (models/order.py)', 'id (PK), order_id (FK orders.id CASCADE), book_id (FK books.id RESTRICT), title (snapshot), unit_price (Numeric 10,2 snapshot), quantity (CheckConstraint: quantity > 0).'],
    ['reviews', 'Review (models/review.py)', 'id (PK), book_id (FK books.id CASCADE), user_id (FK users.id SET NULL), author_name, rating (CheckConstraint 1..5), text, sentiment (positive/neutral/negative), keywords (JSON field).'],
    ['ai_keys', 'AIKey (models/ai_key.py)', 'id (PK), user_id (FK users.id), provider ("gemini"), label, key_hint, encrypted_key (Text mã hóa Fernet), is_active (Boolean).']
], [1.3, 1.8, 3.9])

# CHƯƠNG 5
h('5. Đặc tả API, Xác thực JWT và Phân quyền RBAC', 1)
p('FastAPI cung cấp hệ thống endpoint chuẩn mực, tự động sinh tài liệu Swagger UI tại /docs và ReDoc tại /redoc:')
bullet('Quy tắc Schema vs Model: Tuyệt đối không dùng Model ORM để trả thẳng dữ liệu ra API. Hệ thống xây dựng riêng các Pydantic Schema (schemas/auth.py, book.py, order.py, user.py...). Nhờ có response_model, các trường nhạy cảm như hashed_password hoặc encrypted_key tự động bị loại bỏ hoàn toàn khỏi JSON trả về.')
bullet('Quy tắc URL & Định tuyến: Các route tĩnh (ví dụ: /books/categories, /books/stats) luôn được khai báo trước route động có tham số (như /books/{book_id}) để tránh lỗi xung đột định tuyến.')
bullet('Quy tắc Mã trạng thái HTTP: Tuân thủ đúng chuẩn REST: 200 OK cho truy vấn thành công, 201 Created khi tạo mới (Order, User, Review), 204 No Content khi xóa (AI Key), 400 Bad Request cho lỗi nghiệp vụ (hết hàng), 401 Unauthorized khi thiếu token, 403 Forbidden khi sai quyền, 404 Not Found khi không tìm thấy bản ghi, 422 Unprocessable Entity khi dữ liệu gửi lên sai schema.')

# CHƯƠNG 6
h('6. Phân hệ AI: Phân tích cảm xúc, Khuyến nghị & Kết nối LLM Gemini', 1)
p('Hệ thống AI của BookStore Pro được thiết kế theo tư duy Hybrid thông minh, bảo đảm tính sẵn sàng cao trong mọi điều kiện demo:')
bullet('1. Tầng Khuyến nghị & Chat Heuristic nội bộ (Offline Recommender): File recommender.py phân tích lịch sử mua hàng của người dùng (collaborative signal), lọc sách cùng thể loại độc giả yêu thích, tính điểm phổ biến (popularity từ OrderItem) và so khớp từ khóa/ngân sách bằng Regex. Chatbot tự động trả lời sách phù hợp ngay cả khi không có kết nối Internet.')
bullet('2. Tầng Kết nối LLM Đám mây (Cloud Gemini Integration): File llm_chat.py sử dụng giao thức OpenAI-compatible endpoint kết nối mô hình Google Gemini 3.5 Flash. System Prompt nghiêm ngặt bắt buộc mô hình chỉ được tư vấn sách có trong danh mục CATALOG truyền kèm (Anti-Hallucination), trả về định dạng JSON thuần gồm reply, danh sách book_ids và câu hỏi gợi ý tiếp theo.')
bullet('3. Cơ chế Bảo mật AI Key (Fernet Symmetric Encryption): Khi Admin nhập Gemini API Key trên giao diện /admin/ai-keys, hệ thống không băm (hashing) vì băm một chiều không thể khôi phục lại key để gọi API. Thay vào đó, backend sử dụng thuật toán Fernet (thư viện cryptography) dẫn xuất từ SECRET_KEY hệ thống để mã hóa đối xứng. Database chỉ lưu encrypted_key và key_hint (ví dụ: AIza...38a).')

# CHƯƠNG 7
h('7. Frontend: Kiến trúc React 19 SPA, State Management & Views', 1)
p('Frontend được tái cấu trúc hoàn toàn sang React 19 hiện đại, đóng gói bằng Vite siêu tốc:')
table(['Tệp tin Frontend', 'Vai trò kỹ thuật', 'Chi tiết hiện thực'], [
    ['frontend/src/main.jsx', 'Điểm khởi tạo React', 'Mount React Root vào thẻ div id="root" trong index.html; kích hoạt StrictMode.'],
    ['frontend/src/App.jsx', 'Bộ điều phối ứng dụng', 'Khai báo bảng danh mục ROUTES; kiểm tra phân quyền Route Guard (requiresAuth, requiresAdmin); chọn hiển thị Shell tương ứng (StoreShell, AdminShell, AuthShell); quản lý toast thông báo toàn cục.'],
    ['frontend/src/router.js', 'Hash Router tùy biến', 'Quản lý điều hướng qua hash URL (#/, #/catalog, #/book/:id, #/admin...). Cung cấp hook useHashLocation() và các hàm navigate(), rewriteUrl() mượt mà.'],
    ['frontend/src/store.js', 'Quản lý trạng thái toàn cục', 'Sử dụng cơ chế Observer Pattern kết hợp hook useSyncExternalStore của React. Quản lý đồng bộ trạng thái token, thông tin user và giỏ hàng (cart); tự động lưu bền vững vào LocalStorage.'],
    ['frontend/src/api.js', 'API Client trung tâm', 'Module duy nhất nắm toàn bộ endpoint Backend; tự động chèn header Bearer token; chuyển đổi mã lỗi HTTP thành ApiError có cấu trúc rõ ràng.'],
    ['frontend/src/ui.jsx', 'Thư viện UI tái sử dụng', 'Cung cấp các component cốt lõi: BookCard, Stars, ToastHost, Modal, Drawer giỏ hàng, hàm định dạng tiền tệ money().'],
    ['frontend/src/views/HomeView.jsx', 'Trang chủ website', 'Hiển thị Hero Banner, danh mục thể loại nổi bật, sách mới cập nhật và sách bán chạy.'],
    ['frontend/src/views/CatalogView.jsx', 'Trang duyệt danh mục', 'Tìm kiếm real-time có debounce, lọc thể loại, lọc khoảng giá, sắp xếp đa chiều và phân trang động.'],
    ['frontend/src/views/BookView.jsx', 'Trang chi tiết ấn phẩm', 'Hiển thị thông tin sách, ảnh bìa, mô tả, nút thêm giỏ hàng có kiểm tra tồn kho, danh sách bình luận kèm phân tích cảm xúc và form gửi đánh giá mới.'],
    ['frontend/src/views/AuthView.jsx', 'Trang Đăng nhập / Đăng ký', 'Biểu mẫu xác thực mượt mà, tích hợp nút đăng nhập nhanh 1-click cho tài khoản mẫu Admin và Customer demo.'],
    ['frontend/src/views/OrdersView.jsx', 'Trang Lịch sử đơn hàng', 'Danh sách các đơn hàng của khách hàng hiện tại, chi tiết từng cuốn sách và trạng thái giao hàng.'],
    ['frontend/src/views/AiView.jsx', 'Màn hình AI Reading Room', 'Giao diện chat trực quan với trợ lý sách ảo; hỗ trợ các gợi ý nhanh (chips); danh sách sách gợi ý có thể click xem chi tiết hoặc thêm giỏ ngay.'],
    ['frontend/src/views/admin/*', 'Trang Quản trị hệ thống', 'Phân hệ quản trị toàn diện gồm 8 view: Overview, Books (CRUD), Orders (Đổi trạng thái), Customers (Phân quyền role), Reviews (Kiểm duyệt), AiKeys (Quản lý Gemini key), Analytics (Biểu đồ doanh thu KPI).']
], [2.0, 1.8, 3.2])

# CHƯƠNG 8
h('8. Đóng gói Container, Vận hành Docker và Mở rộng Kubernetes/Power BI', 1)
p('Toàn bộ hệ thống được container hóa chuyên nghiệp, bảo đảm chạy đồng nhất trên mọi hệ điều hành:')
bullet('Khởi động toàn bộ với 1 lệnh duy nhất: docker compose up -d --build')
bullet('Container 1 - bookstore-postgres: Chạy PostgreSQL 16 Alpine, ánh xạ cổng 5433 ở máy host (để không đụng port 5432 mặc định), dữ liệu được giữ an toàn trên Docker Volume bookstore_pgdata.')
bullet('Container 2 - bookstore-api: Chạy FastAPI trên python:3.12-slim, phục vụ REST API tại cổng 8000, có healthcheck tự động thăm dò endpoint /health.')
bullet('Container 3 - bookstore-frontend: Build tĩnh React SPA và đóng gói vào image Nginx 1.27 Alpine, phục vụ website tại cổng 3000. Tệp nginx.conf cấu hình try_files để hỗ trợ Single Page Application và thiết lập reverse proxy định tuyến /api sang container api.')
bullet('Mở rộng Kubernetes (k8s/): Cung cấp đầy đủ các manifest: postgres-statefulset.yaml (đảm bảo tính toàn vẹn storage), api-deployment.yaml, frontend-deployment.yaml và ingress.yaml phục vụ triển khai môi trường Cloud.')
bullet('Mở rộng Power BI (powerbi/documentation.md): Cung cấp tài liệu mô hình dữ liệu báo cáo chuyên sâu phục vụ phân tích kinh doanh đa chiều.')

# CHƯƠNG 9
h('9. Bản đồ giải thích toàn bộ tệp tin trong Repository', 1)
table(['Thư mục / Tệp tin', 'Phân loại', 'Giải thích khi hội đồng hỏi tới'], [
    ['run.py', 'Launcher tiện ích', 'Script tự động hóa bằng Python: kiểm tra port, bật container postgres ngầm nếu cần, kích hoạt uvicorn và tự động mở trình duyệt web. Có cờ --sqlite để chạy demo offline không cần Docker.'],
    ['start.bat', 'Lối tắt Windows', 'Tệp batch tiện lợi cho phép người dùng click đúp trên Windows để khởi động toàn bộ dự án.'],
    ['backend/create_admin.py', 'CLI Quản trị', 'Script dòng lệnh dùng để tạo mới hoặc thăng cấp tài khoản bất kỳ thành quyền Admin trực tiếp trong database.'],
    ['backend/app/db/init_db.py', 'Khởi tạo CSDL', 'Tự động tạo các bảng (create_all) và nạp dữ liệu mẫu ban đầu (100 đầu sách, thể loại, tài khoản demo) nếu cơ sở dữ liệu còn trống.'],
    ['backend/app/db/mock_data.py', 'Dữ liệu mẫu Fixture', 'Kho dữ liệu 100 đầu sách IT kinh điển dùng cho quá trình seed dữ liệu thử nghiệm ban đầu.'],
    ['backend/test/test_auth.py', 'Kiểm thử Unit Test', 'Bộ kiểm thử Pytest tự động kiểm tra tính đúng đắn của luồng đăng ký, đăng nhập và phân quyền bảo mật.']
], [2.2, 1.8, 3.0])

# CHƯƠNG 10
h('10. Kịch bản thuyết trình Live Demo 8-10 phút gây ấn tượng hội đồng', 1)
p('Hãy trình bày tự tin theo đúng tiến trình của một sản phẩm thương mại thực tế:')
table(['Thời gian', 'Thao tác trên màn hình', 'Lời thoại thuyết trình chuẩn mực (Nói rõ hành động - API - Dữ liệu)'], [
    ['0:00 - 1:00', 'Mở trang chủ http://localhost:3000', '“Kính thưa Hội đồng, em xin trình bày dự án BookStore Pro – nền tảng kinh doanh sách lập trình và CNTT, được kiến trúc theo mô hình Fullstack phân tầng với Frontend React 19 SPA và Backend FastAPI RESTful API.”'],
    ['1:00 - 2:30', 'Vào Catalog: gõ tìm kiếm, lọc thể loại, sang trang', '“Tại màn hình Catalog, mỗi thao tác gõ phím được debounce 260ms để tối ưu tải; request gửi đến GET /api/v1/books, Backend lọc trực tiếp trên PostgreSQL Index và trả về kết quả phân trang kèm tổng số bản ghi.”'],
    ['2:30 - 4:00', 'Bấm Thêm vào giỏ, mở Cart Drawer, bấm Checkout', '“Giỏ hàng được quản lý phản ứng nhanh tại Client qua useSyncExternalStore. Khi bấm thanh toán, request POST /api/v1/orders được gửi đi. Backend mở một Database Transaction, sử dụng with_for_update khóa bản ghi để chống mua vượt tồn kho (Race condition), trừ stock và snapshot giá mua vào bảng order_items.”'],
    ['4:00 - 5:30', 'Vào chi tiết sách, gửi đánh giá 5 sao', '“Khách hàng gửi nhận xét kèm đánh giá sao. Backend lập tức kích hoạt module NLP analyze_sentiment để phân tích từ ngữ tích cực/tiêu cực, tự động gắn nhãn sentiment và trích xuất từ khóa lưu vào trường JSON của database.”'],
    ['5:30 - 7:00', 'Mở màn hình AI Reading Room (/ai)', '“Tại phòng đọc AI, khách hàng có thể trò chuyện tự nhiên để tìm sách theo trình độ và ngân sách. Hệ thống áp dụng cơ chế Hybrid: mặc định sử dụng Rule-based Recommender trên catalog thật; khi Admin kích hoạt Gemini Key, hệ thống sẽ kết nối mô hình Google Gemini 3.5 Flash với System Prompt chống ảo giác (Anti-Hallucination).”'],
    ['7:00 - 8:30', 'Đăng nhập Admin demo, mở /admin/analytics và /admin/books', '“Em chuyển sang trang quản trị Admin. Mọi API /api/v1/admin/* đều được bảo vệ nghiêm ngặt bằng JWT Role Admin ở Backend. Admin có thể CRUD sách, cập nhật trạng thái đơn hàng (tự động hoàn kho nếu hủy), quản lý phân quyền khách hàng và theo dõi biểu đồ doanh thu KPI.”'],
    ['8:30 - 9:30', 'Mở terminal hiển thị Docker Compose', '“Hệ thống được đóng gói hoàn chỉnh bằng Docker Compose gồm 3 container: PostgreSQL, API FastAPI và Frontend Nginx. Toàn bộ kiến trúc đều hướng tới tính module hóa, an toàn dữ liệu và khả năng mở rộng cao.”']
], [1.2, 2.3, 3.5])

# CHƯƠNG 11
h('11. Bộ 20 câu hỏi phản biện thường gặp và Đáp án chuẩn xác', 1)
qa_list = [
    ['1. Sự khác biệt giữa Pydantic Schema và SQLAlchemy Model?', 'Model ánh xạ cấu trúc bảng trong PostgreSQL (có khóa chính, khóa ngoại, constraint). Schema là bản hợp đồng dữ liệu JSON qua API (xác thực kiểu dữ liệu đầu vào và lọc bỏ thông tin nhạy cảm ở đầu ra như hashed_password).'],
    ['2. Tại sao phải sử dụng SELECT ... FOR UPDATE khi đặt hàng?', 'Để ngăn chặn race condition khi nhiều người cùng mua sách cuối cùng trong kho. Lệnh này khóa dòng dữ liệu trong transaction cho đến khi commit, bảo đảm không bao giờ bị âm kho.'],
    ['3. Tại sao bảng order_items phải lưu lại unit_price và title?', 'Đây là kỹ thuật Snapshot giá lịch sử. Nếu trong tương lai Admin đổi giá hoặc sửa tên sách trong bảng books, lịch sử và tổng tiền của các đơn hàng cũ trong quá khứ vẫn được bảo toàn nguyên vẹn.'],
    ['4. Tại sao API Key của Gemini lại mã hóa đối xứng (Fernet) thay vì băm (Argon2)?', 'Mật khẩu chỉ cần kiểm tra khớp nên băm một chiều. API Key phải được Backend giải mã nguyên vẹn để gửi request xác thực tới máy chủ Google Gemini, do đó bắt buộc phải dùng thuật toán mã hóa đối xứng hai chiều.'],
    ['5. Cơ chế phân quyền được bảo vệ ở Frontend hay Backend?', 'Bảo vệ tuyệt đối ở Backend qua FastAPI dependency (get_current_admin). Nút ẩn/hiện và route guard trên Frontend chỉ là tối ưu trải nghiệm người dùng; người dùng cố tình gửi request trực tiếp bằng Postman/curl vẫn bị Backend chặn mã lỗi 403 Forbidden.'],
    ['6. Dự án xử lý lỗi CORS như thế nào?', 'Khi chạy Docker hoặc Production, Nginx đóng vai trò Reverse Proxy phục vụ cùng một Origin (domain/port) và chuyển hướng /api/v1 sang Backend nên không phát sinh CORS. Khi dev cục bộ, FastAPI được cấu hình middleware CORSMiddleware cho phép Frontend truy cập.'],
    ['7. Trợ lý AI có bịa đặt (hallucinate) thông tin sách không?', 'Không. Cả hai tầng AI đều được ràng buộc chặt chẽ: tầng Rule-based chỉ lấy sách từ database; tầng LLM Gemini được truyền ngữ cảnh CATALOG thực tế kèm câu lệnh System Prompt cấm tuyệt đối việc tự bịa sách, giá hoặc số lượng tồn kho.']
]
table(['Câu hỏi phản biện', 'Câu trả lời gãy gọn, ghi điểm tối đa'], qa_list, [2.5, 4.5])

# CHƯƠNG 12
h('12. Phiếu ôn tập nhanh 15 phút trước khi bước vào phòng thi', 1)
p('Dành 15 phút cuối cùng trước khi vào phòng chấm để rà soát lại 5 trọng điểm cốt lõi:')
bullet('Phút 1-3: Nhắm mắt vẽ lại sơ đồ kiến trúc: Trình duyệt React 19 -> Nginx:3000 -> FastAPI:8000 -> SQLAlchemy -> PostgreSQL:5433.')
bullet('Phút 4-6: Ôn lại luồng đặt hàng: "Checkout -> POST /orders -> with_for_update khóa stock -> tạo Order + OrderItem -> trừ stock -> commit".')
bullet('Phút 7-9: Ôn lại cơ chế bảo mật: "Mật khẩu băm Argon2, Token JWT HMAC-SHA256, API Key mã hóa Fernet AES-128".')
bullet('Phút 10-12: Mở terminal chạy thử lệnh "python run.py --sqlite --no-browser" để chắc chắn máy luôn có sẵn một bản backup chạy mượt mà không lo sự cố mạng.')
bullet('Phút 13-15: Ghi nhớ tài khoản demo: Admin (admin@bookstorepro.com / admin-password-123) và Customer (customer@bookstorepro.com / customer-password-123).')

p('Chúc bạn có một buổi bảo vệ đồ án thành công rực rỡ và đạt điểm số xuất sắc!')

# FOOTER
for section in doc.sections:
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rf = footer.add_run('Sách học & Thuyết trình BookStore Pro - FPT Aptech | Trang ')
    rf.font.size = Pt(8.5)
    rf.font.color.rgb = RGBColor(120, 120, 120)

# Save to updated file
doc.save(OUT_UPDATED)
print(f'Document successfully generated and saved to: {OUT_UPDATED.resolve()}')

# Try overwriting original if unlocked
try:
    doc.save(OUT_ORIGINAL)
    print(f'Original file successfully updated: {OUT_ORIGINAL.resolve()}')
except Exception as e:
    print(f'Note: Could not overwrite original file because it is open in Word ({e}). It has been written to {OUT_UPDATED.name}!')

