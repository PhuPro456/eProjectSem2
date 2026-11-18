import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

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

def build_srs():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.75)
    sec.bottom_margin = Inches(0.75)
    sec.left_margin = Inches(0.75)
    sec.right_margin = Inches(0.75)

    styles = doc.styles
    styles['Normal'].font.name = 'Aptos'
    styles['Normal'].font.size = Pt(10)
    styles['Normal'].paragraph_format.space_after = Pt(4)
    styles['Normal'].paragraph_format.line_spacing = 1.15

    for n, size, col in [('Title', 22, '0F2D24'), ('Heading 1', 14, '154734'), ('Heading 2', 12, '1E5A44'), ('Heading 3', 10.5, '2A6F54')]:
        s = styles[n]
        s.font.name = 'Aptos Display'
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = RGBColor.from_string(col)

    def add_p(text='', boldlead=None, italic=False):
        x = doc.add_paragraph()
        if boldlead:
            r = x.add_run(boldlead)
            r.bold = True
        r2 = x.add_run(text)
        r2.italic = italic
        return x

    def add_h(text, level=1):
        p = doc.add_heading(text, level=level)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        return p

    def add_bullet(text, level=0):
        x = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
        x.paragraph_format.space_after = Pt(2)
        x.add_run(text)
        return x

    def add_table(headers, rows, widths=None):
        t = doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.style = 'Table Grid'
        borders(t)
        for i, h in enumerate(headers):
            shade(t.rows[0].cells[i], '154734')
            set_cell(t.rows[0].cells[i], h, bold=True, color='FFFFFF', font_size=9)
        for n, row in enumerate(rows):
            cells = t.add_row().cells
            bg = 'F8FAF9' if n % 2 == 1 else 'FFFFFF'
            for i, val in enumerate(row):
                shade(cells[i], bg)
                set_cell(cells[i], str(val), font_size=8.5)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        doc.add_paragraph()
        return t

    # HEADER & TITLE
    p_title = doc.add_paragraph(style='Title')
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.add_run('TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)\nBOOKSTORE PRO - FULLSTACK E-COMMERCE & AI ASSISTANT')

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run('Hệ thống Quản lý Kinh doanh Sách Trực tuyến Tích hợp Trợ lý Trí tuệ Nhân tạo AI Reading Room')
    r_sub.italic = True
    r_sub.font.size = Pt(11)

    meta_table = [
        ['Loại tài liệu:', 'Software Requirements Specification (SRS) - Chuẩn Kỹ thuật Phần mềm FPT-Aptech'],
        ['Dự án:', 'BookStore Pro (Fullstack Web Application: React 19 + FastAPI + PostgreSQL + AI)'],
        ['Sinh viên thực hiện:', 'Trần Quốc Phú (Mã số SV: QuocPhu1690422)'],
        ['Phiên bản tài liệu:', '2.0 (Cập nhật đồng bộ 100% Kiến trúc Frontend React SPA & Backend RESTful API)'],
        ['Trạng thái dự án:', 'Hoàn thành phát triển & đóng gói container Docker (Production Ready)'],
        ['Phạm vi hệ thống:', 'Frontend Client/Admin SPA, Backend API, PostgreSQL Engine, Rule & LLM Chatbot, Docker/K8s']
    ]
    add_table(['Thông tin', 'Chi tiết đặc tả'], meta_table, [2.2, 4.8])

    # 1. GIỚI THIỆU
    add_h('1. GIỚI THIỆU (INTRODUCTION)', 1)
    add_h('1.1. Mục đích tài liệu (Purpose)', 2)
    add_p('Tài liệu SRS này xác định đầy đủ các yêu cầu chức năng (Functional Requirements), yêu cầu phi chức năng (Non-Functional Requirements), mô hình kiến trúc hai tầng độc lập Frontend (React 19) và Backend (FastAPI), cơ chế dữ liệu quan hệ (PostgreSQL) và hệ thống hỗ trợ AI cho dự án BookStore Pro.')
    add_p('Tài liệu được sử dụng làm cơ sở pháp lý và kỹ thuật cho: thẩm định bảo vệ đồ án, kiểm thử nghiệm thu (Acceptance Criteria), hướng dẫn vận hành, bảo trì và tích hợp mở rộng.')

    add_h('1.2. Phạm vi dự án (Project Scope)', 2)
    add_p('BookStore Pro là nền tảng thương mại điện tử chuyên ngành sách lập trình, CNTT và khoa học dữ liệu, phục vụ hai nhóm đối tượng chính: Khách hàng trực tuyến (Customer) và Quản trị viên cửa hàng (Admin/Staff). Hệ thống cung cấp chu trình nghiệp vụ khép kín từ duyệt danh mục, tìm kiếm lọc nâng cao, giỏ hàng client-side, đặt hàng transaction an toàn, đánh giá sách phân tích cảm xúc (NLP Sentiment) đến quản trị kho, đơn hàng, khách hàng, cấu hình API key AI và báo cáo doanh thu.')

    add_h('1.3. Định nghĩa và thuật ngữ (Definitions & Acronyms)', 2)
    terms = [
        ['SPA', 'Single Page Application - Ứng dụng web tải một trang duy nhất, điều hướng mượt mà không reload trang qua Hash Router.'],
        ['RESTful API', 'Giao diện lập trình ứng dụng tuân thủ chuẩn REST, trao đổi dữ liệu định dạng JSON chuẩn qua HTTP/HTTPS.'],
        ['JWT', 'JSON Web Token - Chuẩn token xác thực an toàn (RFC 7519) dùng cho Stateless Authentication giữa Frontend và Backend.'],
        ['ORM', 'Object-Relational Mapping - Ánh xạ hướng đối tượng với cơ sở dữ liệu quan hệ (SQLAlchemy 2.0 mapped_column).'],
        ['Pydantic V2', 'Thư viện data validation và serialization hiệu năng cao cho Python, bảo đảm JSON contract toàn diện.'],
        ['Argon2 / pwdlib', 'Thuật toán băm mật khẩu một chiều đạt tiêu chuẩn an toàn bảo mật mật khẩu hiện đại nhất (chống GPU brute-force).'],
        ['Fernet / AES-128', 'Mã hóa đối xứng tiêu chuẩn để lưu trữ an toàn các AI Provider Key (Gemini API Key) trong cơ sở dữ liệu.'],
        ['Vite & React 19', 'Nền tảng build công cụ nhanh và thư viện render UI dạng Declarative Component tiên tiến nhất hiện nay.']
    ]
    add_table(['Thuật ngữ', 'Giải thích chuyên môn'], terms, [1.8, 5.2])

    # 2. TỔNG QUAN KIẾN TRÚC & PHÂN QUYỀN
    add_h('2. TỔNG QUAN HỆ THỐNG VÀ KIẾN TRÚC FULLSTACK', 1)
    add_h('2.1. Mô hình Kiến trúc Phân tầng (Tier Architecture)', 2)
    add_p('Hệ thống được thiết kế theo mô hình tách biệt hoàn toàn Client-Server (Decoupled Fullstack Architecture):')
    add_bullet('Frontend Tier (Client): Xây dựng bằng React 19 SPA, Vite build bundle siêu nhẹ, Vanilla CSS Design System hiện đại không phụ thuộc UI framework nặng. Điều hướng bằng Hash Routing (#/, #/catalog, #/admin...), quản trị trạng thái Client State (auth, user, cart) qua Store Observer phản ứng nhanh (useSyncExternalStore), giao tiếp API bất đồng bộ qua Axios/Fetch Client chuyên dụng.')
    add_bullet('Backend Tier (Server): Xây dựng bằng Python FastAPI (Asynchronous ready), định tuyến module hóa (/api/v1/...), kiểm soát hợp đồng dữ liệu qua Pydantic schemas, dependency injection thông minh (deps.py) cho Database Session và RBAC Authentication.')
    add_bullet('Database Tier (Storage): Hệ quản trị PostgreSQL 16 (triển khai containerized), hỗ trợ SQLite song song cho môi trường dev nhanh. Sử dụng SQLAlchemy ORM với đầy đủ ràng buộc toàn vẹn dữ liệu (CheckConstraint, ForeignKey RESTRICT/CASCADE, Index).')
    add_bullet('AI & Analytics Tier: Module xử lý ngôn ngữ tự nhiên tích hợp (NLP Lexicon Sentiment), Engine gợi ý sách kết hợp (Popularity + Content-based + Budget matching) và cổng kết nối LLM Chatbot (Google Gemini API qua chuẩn OpenAI SDK).')

    add_h('2.2. Ma trận Phân quyền Người dùng (Role-Based Access Control - RBAC)', 2)
    rbac_data = [
        ['Khách vãng lai (Guest)', 'Xem trang chủ, xem danh mục sách, tìm kiếm, lọc theo thể loại/giá, xem chi tiết sách, thêm giỏ hàng (Local Cart), trò chuyện với AI Assistant.'],
        ['Khách hàng đăng nhập (Customer)', 'Toàn bộ quyền của Guest + Đặt hàng trực tuyến, xem lịch sử đơn hàng cá nhân, gửi đánh giá & chấm điểm nhận xét kèm phân tích cảm xúc, nhận gợi ý cá nhân hóa theo lịch sử mua.'],
        ['Quản trị viên (Admin)', 'Toàn bộ quyền của Customer + Truy cập Admin Dashboard (/admin), CRUD sách, xem/thay đổi trạng thái đơn hàng (pending -> paid -> shipped -> completed -> cancelled), quản lý danh sách khách hàng & phân quyền tài khoản, duyệt xóa đánh giá vi phạm, cấu hình & kích hoạt AI API Key, theo dõi biểu đồ thống kê Analytics KPI.']
    ]
    add_table(['Vai trò (Role)', 'Phạm vi Quyền hạn & Chức năng cho phép'], rbac_data, [2.0, 5.0])

    # 3. YÊU CẦU CHỨC NĂNG CHI TIẾT
    add_h('3. YÊU CẦU CHỨC NĂNG HỆ THỐNG (FUNCTIONAL REQUIREMENTS)', 1)
    add_h('3.1. Phân hệ Xác thực & Quản lý Tài khoản (Auth & Identity)', 2)
    auth_reqs = [
        ['FR-AUTH-001', 'Frontend cung cấp màn hình Đăng ký tài khoản (họ tên, email, mật khẩu >= 6 ký tự) và màn hình Đăng nhập tiện lợi (hỗ trợ 1-click Demo Accounts: Admin/Customer).', 'Must Have'],
        ['FR-AUTH-002', 'Backend mã hóa mật khẩu một chiều bằng thuật toán Argon2 trước khi lưu vào bảng users; không bao giờ lưu plain text.', 'Must Have'],
        ['FR-AUTH-003', 'Backend xác thực thành công sẽ ký và cấp JWT Access Token (HS256) chứa user_id, email, role và thời gian hết hạn (expire time).', 'Must Have'],
        ['FR-AUTH-004', 'Frontend lưu trữ Token vào LocalStorage, tự động đính kèm header "Authorization: Bearer <token>" vào mọi API request bảo vệ qua api.js.', 'Must Have'],
        ['FR-AUTH-005', 'Hệ thống hỗ trợ route guard ở cả 2 đầu: Frontend chặn điều hướng trái phép (requiresAuth, requiresAdmin) và Backend xác thực nghiêm ngặt bằng Depends(get_current_user) / Depends(get_current_admin).', 'Must Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], auth_reqs, [1.5, 4.3, 1.2])

    add_h('3.2. Phân hệ Quản lý Sách & Danh mục (Catalog & Inventory)', 2)
    book_reqs = [
        ['FR-BOOK-001', 'Frontend hiển thị Catalog đa chiều: tìm kiếm từ khóa real-time (debounce 260ms), bộ lọc thể loại (Categories), khoảng giá min/max, sắp xếp (mới nhất, giá tăng/giảm, bán chạy, rating).', 'Must Have'],
        ['FR-BOOK-002', 'Trang chi tiết sách (/book/:id): hiển thị ảnh bìa, tác giả, giá tiền, mô tả chi tiết, số lượng tồn kho còn lại, danh sách đánh giá từ cộng đồng.', 'Must Have'],
        ['FR-BOOK-003', 'Admin View: Màn hình CRUD sách chuyên dụng (/admin/books), cho phép thêm sách mới, cập nhật giá/kho/thông tin và xóa sách.', 'Must Have'],
        ['FR-BOOK-004', 'Backend kiểm soát toàn vẹn: Không cho phép giá âm (price >= 0), tồn kho không âm (stock >= 0); Thể loại dùng khóa ngoại ON DELETE RESTRICT bảo vệ dữ liệu sách liên quan.', 'Must Have'],
        ['FR-BOOK-005', 'Hỗ trợ cả 2 phiên bản endpoint truy vấn: Đồng bộ (/books) và Bất đồng bộ High Performance (/books-async) với SQLAlchemy AsyncSession.', 'Should Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], book_reqs, [1.5, 4.3, 1.2])

    add_h('3.3. Phân hệ Giỏ hàng & Xử lý Đơn hàng (Cart & Order Transaction)', 2)
    order_reqs = [
        ['FR-ORD-001', 'Giỏ hàng Client-Side: Lưu trữ trong LocalStorage, drawer giỏ hàng mở trượt mượt mà từ cạnh màn hình, tự động cập nhật số lượng và tổng tiền tức thì.', 'Must Have'],
        ['FR-ORD-002', 'Kiểm tra tồn kho 2 lớp: Frontend chặn không cho thêm vượt stock hiện tại; Backend kiểm tra tuyệt đối bằng Database Row Lock (SELECT ... FOR UPDATE) trong transaction.', 'Must Have'],
        ['FR-ORD-003', 'Snapshot giá tại thời điểm mua: Bảng order_items bắt buộc sao lưu title và unit_price tại thời điểm checkout, bảo đảm giá lịch sử không bị ảnh hưởng nếu sách đổi giá sau này.', 'Must Have'],
        ['FR-ORD-004', 'Trang Đơn hàng của tôi (/orders): Khách hàng đăng nhập xem danh sách các đơn đã đặt, chi tiết từng cuốn sách, giá tiền và trạng thái xử lý.', 'Must Have'],
        ['FR-ORD-005', 'Quản lý đơn hàng Admin (/admin/orders): Admin lọc đơn theo trạng thái (pending, paid, shipped, completed, cancelled) và cập nhật trạng thái đơn; nếu hủy đơn, hệ thống tự động hoàn kho (Restock) chính xác.', 'Must Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], order_reqs, [1.5, 4.3, 1.2])

    add_h('3.4. Phân hệ Đánh giá Sách & Phân tích Cảm xúc (Reviews & NLP Sentiment)', 2)
    rev_reqs = [
        ['FR-REV-001', 'Khách hàng đã đăng nhập có thể gửi đánh giá từ 1 đến 5 sao và viết nhận xét văn bản cho bất kỳ cuốn sách nào.', 'Must Have'],
        ['FR-REV-002', 'Tự động phân tích cảm xúc (NLP Sentiment Engine): Khi nhận bài đánh giá, backend tự động phân tích từ vựng (positive, neutral, negative) và trích xuất từ khóa nổi bật (keywords).', 'Must Have'],
        ['FR-REV-003', 'Màn hình Quản trị Đánh giá (/admin/reviews): Admin theo dõi biểu đồ tỷ lệ cảm xúc độc giả và có quyền xóa các đánh giá spam/vi phạm.', 'Must Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], rev_reqs, [1.5, 4.3, 1.2])

    add_h('3.5. Phân hệ Trợ lý AI & Quản lý AI Key (AI Reading Room & LLM Integration)', 2)
    ai_reqs = [
        ['FR-AI-001', 'Màn hình AI Reading Room (/ai): Cung cấp giao diện chat chuyên nghiệp, các prompt gợi ý nhanh (chips), danh sách sách đề xuất đi kèm có thể click mua ngay.', 'Must Have'],
        ['FR-AI-002', 'Cơ chế AI Hybrid 2 lớp (Local Heuristic + Cloud LLM): Hoạt động offline mượt mà bằng engine so khớp catalog/budget; khi có AI Key hợp lệ sẽ nâng cấp lên Google Gemini 3.5 Flash.', 'Must Have'],
        ['FR-AI-003', 'Bảo mật Quản lý AI Key (/admin/ai-keys): Admin nhập API key, Backend mã hóa đối xứng Fernet trước khi lưu database; chỉ hiển thị key hint (sk-...9f2a), có nút kích hoạt và kiểm tra định dạng (Verify).', 'Must Have'],
        ['FR-AI-004', 'Chống bịa đặt (Anti-Hallucination Guardrail): System prompt bắt buộc LLM chỉ được giới thiệu sách có thực trong danh mục kèm ID/giá/stock chính xác từ database.', 'Must Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], ai_reqs, [1.5, 4.3, 1.2])

    add_h('3.6. Phân hệ Báo cáo Doanh thu & Quản lý Khách hàng (Analytics & CRM)', 2)
    admin_reqs = [
        ['FR-ADM-001', 'Admin Analytics (/admin/analytics): Cung cấp 4 thẻ chỉ số KPI cốt lõi (Tổng doanh thu, Đơn hàng, Giá trị trung bình/đơn AOV, Sách đã bán) kèm biểu đồ phân bổ doanh thu theo tháng, thể loại và trạng thái.', 'Must Have'],
        ['FR-ADM-002', 'Quản lý Khách hàng (/admin/customers): Danh sách toàn bộ người dùng, số đơn đã mua, tổng chi tiêu, ngày đăng ký và tính năng phân quyền (chuyển đổi vai trò customer <-> admin).', 'Must Have']
    ]
    add_table(['Mã Yêu Cầu', 'Mô tả Chi tiết Yêu cầu Chức năng', 'Độ Ưu Tiên'], admin_reqs, [1.5, 4.3, 1.2])

    # 4. YÊU CẦU DỮ LIỆU & DATABASE SCHEMA
    add_h('4. YÊU CẦU DỮ LIỆU VÀ LƯỢC ĐỒ CƠ SỞ DỮ LIỆU (DATABASE SCHEMA)', 1)
    add_p('Cơ sở dữ liệu được thiết kế chuẩn hóa 3NF, bảo đảm tính toàn vẹn quan hệ và tốc độ truy vấn tối ưu:')
    schema_data = [
        ['users', 'Lưu trữ thông tin người dùng và phân quyền RBAC.', 'id (PK), name, email (UQ, IDX), hashed_password, role, is_active, created_at'],
        ['categories', 'Danh mục thể loại sách chuẩn hóa.', 'code (PK, VARCHAR 50), name (UQ, VARCHAR 100)'],
        ['books', 'Thông tin chi tiết ấn phẩm sách trong cửa hàng.', 'id (PK), title (IDX), author (IDX), category_code (FK categories.code), description, price (Numeric 10,2), stock (INT), cover (VARCHAR 255)'],
        ['orders', 'Đơn đặt hàng của khách hàng.', 'id (PK), user_id (FK users.id CASCADE), status (CheckConstraint), total (Numeric 12,2), created_at'],
        ['order_items', 'Chi tiết các đầu sách trong từng đơn hàng.', 'id (PK), order_id (FK orders.id CASCADE), book_id (FK books.id RESTRICT), title, quantity (INT > 0), unit_price (Numeric 10,2)'],
        ['reviews', 'Đánh giá nhận xét của độc giả về từng cuốn sách.', 'id (PK), book_id (FK books.id CASCADE), user_id (FK users.id SET NULL), author_name, rating (1..5), text, sentiment, keywords (JSON), created_at'],
        ['ai_keys', 'Quản lý các API Key kết nối nhà cung cấp AI.', 'id (PK), user_id (FK users.id), provider ("gemini"), label, key_hint, encrypted_key (Text Fernet), is_active (BOOL), created_at']
    ]
    add_table(['Tên Bảng (Table)', 'Mục đích Nghiệp vụ', 'Các Trường Dữ liệu & Ràng buộc Chính'], schema_data, [1.5, 2.5, 3.0])

    # 5. ĐẶC TẢ GIAO DIỆN API (API SPECIFICATION)
    add_h('5. ĐẶC TẢ GIAO DIỆN LẬP TRÌNH API (API SPECIFICATION)', 1)
    add_p('Hệ thống cung cấp danh mục API chuẩn RESTful tại tiền tố /api/v1 với tài liệu Swagger UI tự động tại /docs:')
    api_endpoints = [
        ['POST', '/api/v1/auth/register', 'Đăng ký tài khoản người dùng mới', 'Public'],
        ['POST', '/api/v1/auth/login', 'Đăng nhập hệ thống & cấp JWT Token', 'Public'],
        ['GET', '/api/v1/auth/me', 'Lấy thông tin tài khoản đang đăng nhập', 'Customer/Admin'],
        ['GET', '/api/v1/books', 'Lấy danh sách sách có tìm kiếm, lọc & phân trang', 'Public'],
        ['GET', '/api/v1/books/{id}', 'Xem thông tin chi tiết một cuốn sách', 'Public'],
        ['POST', '/api/v1/books', 'Thêm mới một cuốn sách vào kho', 'Admin only'],
        ['PATCH', '/api/v1/books/{id}', 'Cập nhật giá, số lượng tồn kho, mô tả', 'Admin only'],
        ['DELETE', '/api/v1/books/{id}', 'Xóa cuốn sách khỏi hệ thống', 'Admin only'],
        ['GET', '/api/v1/orders', 'Lấy danh sách đơn hàng của người dùng hiện tại', 'Customer/Admin'],
        ['POST', '/api/v1/orders', 'Tạo đơn hàng mới (Trừ kho an toàn qua Transaction)', 'Customer/Admin'],
        ['GET', '/api/v1/admin/orders', 'Danh sách toàn bộ đơn hàng trong hệ thống', 'Admin only'],
        ['PATCH', '/api/v1/admin/orders/{id}/status', 'Cập nhật trạng thái đơn hàng (Hoàn kho nếu hủy)', 'Admin only'],
        ['POST', '/api/v1/books/{id}/reviews', 'Gửi đánh giá sách & phân tích cảm xúc NLP', 'Customer/Admin'],
        ['GET', '/api/v1/ai/recommendations', 'Lấy danh sách sách đề xuất thông minh', 'Public'],
        ['POST', '/api/v1/ai/chat', 'Trò chuyện hỏi đáp sách với AI Assistant', 'Public'],
        ['GET', '/api/v1/admin/analytics/overview', 'Lấy số liệu KPI và biểu đồ doanh thu', 'Admin only'],
        ['GET', '/api/v1/ai-keys', 'Danh sách các AI Key đã lưu (ẩn secret)', 'Admin only'],
        ['POST', '/api/v1/ai-keys/{id}/verify', 'Kiểm tra tính hợp lệ của AI Key', 'Admin only']
    ]
    add_table(['Phương thức', 'Đường dẫn Endpoint', 'Mục đích Nghiệp vụ', 'Quyền Hạn'], api_endpoints, [1.1, 2.7, 2.1, 1.1])

    # 6. YÊU CẦU PHI CHỨC NĂNG
    add_h('6. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)', 1)
    nfr_data = [
        ['NFR-SEC-001', 'Bảo mật Mật khẩu & Token', 'Mật khẩu băm một chiều với Argon2. JWT Token ký thuật toán HMAC-SHA256 bí mật tối thiểu 32 ký tự, lưu an toàn phía Client.'],
        ['NFR-SEC-002', 'Bảo mật AI Key', 'API Key của bên thứ 3 (Gemini) được mã hóa bằng thuật toán đối xứng Fernet (AES-128-CBC với HMAC authentication).'],
        ['NFR-PERF-001', 'Thời gian Phản hồi API', 'API truy vấn thông thường (Catalog, Books, Auth) phản hồi dưới 150ms trên máy chủ tiêu chuẩn; hỗ trợ endpoint async cho tải cao.'],
        ['NFR-PERF-002', 'Tối ưu Tải Frontend', 'Vite Bundle đóng gói code splitting; các file tĩnh (static covers) được cache tối đa trên Nginx; debounce tìm kiếm 260ms tránh flood API.'],
        ['NFR-DATA-001', 'Toàn vẹn Dữ liệu', 'Sử dụng triệt để ACID Transaction cho toàn bộ thao tác đặt hàng, trừ tồn kho và hoàn kho; loại bỏ hoàn toàn nguy cơ race condition.'],
        ['NFR-DEP-001', 'Đóng gói & Khả chuyển', 'Toàn bộ hệ thống chạy nhất quán bằng Docker Compose (PostgreSQL + FastAPI + Nginx React SPA) hoặc chạy tiện lợi 1 lệnh qua run.py.']
    ]
    add_table(['Mã NFR', 'Tiêu chuẩn', 'Chi tiết Đặc tả Kỹ thuật'], nfr_data, [1.3, 1.8, 3.9])

    # 7. HƯỚNG DẪN TRIỂN KHAI & ĐÓNG GÓI DOCKER
    add_h('7. ĐẶC TẢ TRIỂN KHAI VÀ VẬN HÀNH (DEPLOYMENT SPECIFICATION)', 1)
    add_p('Hệ thống hỗ trợ 2 phương thức triển khai chính thức phù hợp cho cả kiểm thử phát triển và bảo vệ đồ án thực tế:')
    add_bullet('Phương thức 1 - Chạy One-Click bằng Python Launcher: Lệnh "python run.py" tự động phát hiện môi trường ảo (.venv), khởi động container PostgreSQL ngầm nếu cần, kích hoạt server Uvicorn và tự động mở trình duyệt web. Nếu muốn chạy độc lập không cần Docker, chỉ cần gõ "python run.py --sqlite".')
    add_bullet('Phương thức 2 - Triển khai Độc lập Toàn diện bằng Docker Compose: Lệnh "docker compose up -d --build" sẽ khởi động 3 container độc lập liên kết qua mạng bridge nội bộ:')
    add_bullet('  + bookstore-postgres: CSDL PostgreSQL 16 Alpine, lưu dữ liệu bền vững qua Named Volume bookstore_pgdata, có healthcheck pg_isready.')
    add_bullet('  + bookstore-api: Ứng dụng Backend FastAPI chạy trên nền python:3.12-slim, phục vụ API tại cổng 8000.')
    add_bullet('  + bookstore-frontend: Ứng dụng Frontend React được build tĩnh và phục vụ bởi Nginx 1.27 Alpine tại cổng 3000, cấu hình Nginx reverse proxy định tuyến /api sang container backend.')
    add_bullet('Hệ thống cũng cung cấp sẵn các tệp cấu hình Kubernetes (k8s/api-deployment.yaml, frontend-deployment.yaml, postgres-statefulset.yaml, ingress.yaml) và tài liệu Power BI (powerbi/documentation.md) phục vụ mở rộng.')

    # 8. TIÊU CHÍ NGHIỆM THU
    add_h('8. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)', 1)
    ac_data = [
        ['AC-001', 'Đăng ký, Đăng nhập & RBAC', 'Đăng nhập tài khoản Admin vào được /admin; tài khoản Customer bị từ chối chuyển hướng an toàn về trang chủ.'],
        ['AC-002', 'Tìm kiếm & Đặt hàng Trực tuyến', 'Tìm kiếm sách ra đúng kết quả, thêm vào giỏ hàng và đặt hàng thành công; số lượng tồn kho trong database lập tức giảm tương ứng.'],
        ['AC-003', 'Bảo vệ Cạnh tranh Tồn kho', 'Hai yêu cầu đặt hàng cùng lúc vượt quá số lượng stock sẽ bị hệ thống từ chối an toàn nhờ transaction with_for_update.'],
        ['AC-004', 'Phân tích Cảm xúc Đánh giá', 'Đánh giá bình luận có chứa từ tích cực được gán nhãn "positive", từ tiêu cực được gán nhãn "negative" trên giao diện Admin.'],
        ['AC-005', 'Hội thoại AI & Khuyến nghị Sách', 'AI Chatbot trả lời thông minh dựa trên danh mục sách thực tế, gợi ý sách đúng chủ đề/ngân sách của người dùng.'],
        ['AC-006', 'Vận hành Docker Hoàn chỉnh', 'Chạy "docker compose up -d" cả 3 dịch vụ đều đạt trạng thái Healthy và truy cập trơn tru tại http://localhost:3000.']
    ]
    add_table(['Mã AC', 'Nghiệp vụ Kiểm thử', 'Tiêu chí Đạt (Pass)'], ac_data, [1.0, 2.0, 4.0])

    # FOOTER
    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rf = footer.add_run('Tài liệu Đặc tả SRS - Đồ án BookStore Pro | Trang ')
        rf.font.size = Pt(8.5)
        rf.font.color.rgb = RGBColor(120, 120, 120)

    doc.save('Tai_Lieu_SRS_QuocPhu1690422.docx')
    print('SRS written successfully to Tai_Lieu_SRS_QuocPhu1690422.docx')

if __name__ == '__main__':
    build_srs()

