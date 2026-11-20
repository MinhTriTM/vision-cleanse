# -*- coding: utf-8 -*-
"""Build DOCX report: Bo loc Sobel va tich hop vao VisionCleanse."""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json
from pathlib import Path

BASE = Path('/home/hatch/workspace/BaoCao-Sobel-XuLyAnh')
FIG = BASE / 'figures'
RESULTS = json.loads((BASE / 'experiment' / 'results.json').read_text())

doc = Document()

# ---------- page + base styles ----------
sec = doc.sections[0]
sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
sec.left_margin = Cm(3.0); sec.right_margin = Cm(2.0)

st = doc.styles['Normal']
st.font.name = 'Times New Roman'
st.font.size = Pt(13)
st.paragraph_format.line_spacing = 1.3
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
rpr = st.element.get_or_add_rPr(); rf = rpr.get_or_add_rFonts()
rf.set(qn('w:eastAsia'), 'Times New Roman')

for name, size, color, before, after in [
    ('Heading 1', 16, (0x1F, 0x3B, 0x63), 18, 8),
    ('Heading 2', 14, (0x1F, 0x3B, 0x63), 14, 6),
    ('Heading 3', 13, (0x2E, 0x2E, 0x2E), 10, 4),
]:
    s = doc.styles[name]
    s.font.name = 'Times New Roman'; s.font.size = Pt(size); s.font.bold = True
    s.font.color.rgb = RGBColor(*color)
    s.paragraph_format.space_before = Pt(before)
    s.paragraph_format.space_after = Pt(after)
    s.paragraph_format.keep_with_next = True

# footer page number
footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer_p.add_run()
fld1 = OxmlElement('w:fldChar'); fld1.set(qn('w:fldCharType'), 'begin')
instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = 'PAGE'
fld2 = OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'), 'end')
run._r.append(fld1); run._r.append(instr); run._r.append(fld2)

# ---------- helpers ----------
def p(text='', style=None, size=13, bold=False, italic=False, align=None, space_after=6):
    par = doc.add_paragraph(style=style)
    if text:
        r = par.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic
    if align is not None: par.alignment = align
    par.paragraph_format.space_after = Pt(space_after)
    return par

def rich(parts, align=None, space_after=6, style=None):
    """parts: list of (text, bold, italic)"""
    par = doc.add_paragraph(style=style)
    for t, b, i in parts:
        r = par.add_run(t); r.bold = b; r.italic = i
    if align is not None: par.alignment = align
    par.paragraph_format.space_after = Pt(space_after)
    return par

def bullet(text, bold_prefix=None):
    par = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = par.add_run(bold_prefix); r.bold = True
    par.add_run(text)
    par.paragraph_format.space_after = Pt(3)
    return par

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hexcolor); tcPr.append(shd)

def table(headers, rows, widths=None, header_fill='1F3B63'):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        par = hdr[i].paragraphs[0]; r = par.add_run(h)
        r.bold = True; r.font.size = Pt(11); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(hdr[i], header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''
            par = cells[i].paragraphs[0]; r = par.add_run(str(v)); r.font.size = Pt(11)
            par.paragraph_format.space_after = Pt(2)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def caption(text):
    par = doc.add_paragraph()
    r = par.add_run(text); r.italic = True; r.font.size = Pt(11)
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(10)
    return par

def figure(filename, caption_text, width_cm=13.5):
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(str(FIG / filename), width=Cm(width_cm))
    caption(caption_text)

def code_block(code, caption_text=None):
    t = doc.add_table(rows=1, cols=1); t.style = 'Table Grid'
    cell = t.rows[0].cells[0]; shade(cell, 'F2F2F2')
    cell.text = ''
    for j, line in enumerate(code.strip('\n').split('\n')):
        par = cell.paragraphs[0] if j == 0 else cell.add_paragraph()
        r = par.add_run(line if line else ' ')
        r.font.name = 'Consolas'; r.font.size = Pt(9.5)
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.line_spacing = 1.0
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    if caption_text: caption(caption_text)

def callout(title, text):
    t = doc.add_table(rows=1, cols=1); t.style = 'Table Grid'
    cell = t.rows[0].cells[0]; shade(cell, 'EAF1FB')
    cell.text = ''
    par = cell.paragraphs[0]
    r = par.add_run(title); r.bold = True; r.font.size = Pt(12)
    par2 = cell.add_paragraph(); r2 = par2.add_run(text); r2.font.size = Pt(12)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def chapter_break():
    doc.add_page_break()

# =====================================================================
# TRANG BIA
# =====================================================================
p('BỘ GIÁO DỤC VÀ ĐÀO TẠO', size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('TRƯỜNG ĐẠI HỌC ĐỒNG THÁP', size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('KHOA CÔNG NGHỆ VÀ KỸ THUẬT', size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=30)
for _ in range(3): p('', space_after=0)
p('BÁO CÁO HỌC PHẦN XỬ LÝ ẢNH', size=20, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
p('BỘ LỌC SOBEL TRONG PHÁT HIỆN CẠNH', size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p('VÀ TÍCH HỢP VÀO DỰ ÁN VISIONCLEANSE', size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=30)
for _ in range(2): p('', space_after=0)
p('Lớp học phần: ĐHCNTT24A-CS – IN4152N01', size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
p('Giảng viên hướng dẫn: ThS. Trần Ngọc Thuận', size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
p('NHÓM THỰC HIỆN', size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
table(['STT', 'Họ và tên', 'MSSV', 'Vai trò'],
      [['1', 'Đoàn Minh Trí', '0024417136', 'Nhóm trưởng'],
       ['2', 'Lê Tuấn Kiệt', '0024417193', 'Thành viên'],
       ['3', 'Võ Thanh Tân', '0024416594', 'Thành viên'],
       ['4', 'Phạm Thị Như Ý', '0024419356', 'Thành viên']],
      widths=[1.2, 5.5, 4.0, 4.0])
for _ in range(2): p('', space_after=0)
p('Đồng Tháp, năm 2026', size=14, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
chapter_break()

# =====================================================================
# PHAN CONG + MUC LUC
# =====================================================================
p('PHÂN CÔNG NHIỆM VỤ TRONG NHÓM', style='Heading 1')
p('Bảng phân công dưới đây là bản đề xuất của nhóm trưởng, các thành viên có thể điều chỉnh theo thực tế thực hiện.', italic=True)
table(['Thành viên', 'Phần phụ trách chính', 'Sản phẩm'],
      [['Đoàn Minh Trí (nhóm trưởng)', 'Chương 3, Chương 4; tích hợp mã nguồn Sobel vào VisionCleanse; điều phối chung', 'Mã nguồn vòng 2.5, bộ kiểm thử, bản báo cáo hoàn chỉnh'],
       ['Lê Tuấn Kiệt', 'Chương 1: cơ sở lý thuyết chung về xử lý ảnh và lọc không gian', 'Nội dung Chương 1, hình minh họa các phép biến đổi'],
       ['Võ Thanh Tân', 'Chương 2: lý thuyết bộ lọc Sobel, ví dụ tính tay, bảng so sánh', 'Nội dung Chương 2, ví dụ số và bảng so sánh'],
       ['Phạm Thị Như Ý', 'Chương 5, Chương 6; thiết kế slide thuyết trình', 'Số liệu thực nghiệm, file slide, phần kết luận']],
      widths=[4.2, 6.3, 5.0])
chapter_break()

p('MỤC LỤC', style='Heading 1')
toc_items = [
    'MỞ ĐẦU',
    'Chương 1. CƠ SỞ LÝ THUYẾT CHUNG VỀ XỬ LÝ ẢNH VÀ LỌC KHÔNG GIAN',
    'Chương 2. BỘ LỌC SOBEL — LÝ THUYẾT CHUYÊN SÂU',
    'Chương 3. GIỚI THIỆU DỰ ÁN VISIONCLEANSE',
    'Chương 4. TÍCH HỢP BỘ LỌC SOBEL VÀO VISIONCLEANSE (VÒNG 2.5)',
    'Chương 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ',
    'Chương 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN',
    'TÀI LIỆU THAM KHẢO',
    'PHỤ LỤC A. NỘI DUNG SLIDE THUYẾT TRÌNH',
    'PHỤ LỤC B. HƯỚNG DẪN CHẠY DEMO',
]
for it in toc_items:
    par = doc.add_paragraph(); r = par.add_run(it); r.font.size = Pt(13)
    par.paragraph_format.space_after = Pt(4)
p('')
p('DANH MỤC HÌNH', style='Heading 2')
for t in ['Hình 2.1. Kết quả lọc Sobel trên ảnh kiểm thử tổng hợp: ảnh gốc, thành phần Gx, thành phần Gy và độ lớn gradient.',
          'Hình 4.1. Bản đồ cạnh Sobel của ảnh gốc và ảnh âm bản — hai bản đồ giống hệt nhau.',
          'Hình 5.1. Khoảng cách Hamming của pHash, dHash và edge_hash trên các biến thể ảnh.',
          'Hình 5.2. Tỉ lệ năng lượng cạnh (edge_energy) của một số biến thể so với ảnh gốc.']:
    p(t, space_after=3)
p('DANH MỤC BẢNG', style='Heading 2')
for t in ['Bảng 1.1. Các phép lọc làm trơn phổ biến.',
          'Bảng 2.1. So sánh các toán tử phát hiện cạnh bậc nhất và bậc hai.',
          'Bảng 4.1. Các thành phần mã nguồn của vòng 2.5.',
          'Bảng 5.1. Kết quả đo khoảng cách Hamming và tỉ lệ năng lượng cạnh trên 17 trường hợp.']:
    p(t, space_after=3)
chapter_break()

# =====================================================================
# MO DAU
# =====================================================================
p('MỞ ĐẦU', style='Heading 1')
p('Xử lý ảnh (Image Processing) là học phần nền tảng của ngành Công nghệ thông tin, trang bị các kỹ thuật biến đổi và phân tích ảnh số: biến đổi mức xám, lọc không gian, biến đổi miền tần số và các bài toán ứng dụng như phát hiện cạnh, phân đoạn, nhận dạng. Trong các nhóm kỹ thuật đó, phát hiện cạnh bằng đạo hàm bậc nhất là nội dung cốt lõi, vì cạnh chứa phần lớn thông tin cấu trúc của ảnh và là đầu vào của hầu hết các hệ thống thị giác máy tính hiện đại.')
p('Báo cáo này chọn bộ lọc Sobel — toán tử phát hiện cạnh kinh điển do Irwin Sobel và Gary Feldman đề xuất năm 1968 — làm chủ đề nghiên cứu chính. Lý do chọn Sobel không chỉ nằm ở giá trị lý thuyết: nhóm đang phát triển dự án VisionCleanse, một công cụ làm sạch tập dữ liệu thị giác máy tính (loại bỏ ảnh trùng lặp gần đúng và rò rỉ dữ liệu giữa các tập train/val/test). Trong dự án đó, thuật toán dHash vốn dựa trên hiệu độ sáng giữa hai pixel kề — tức một dạng gradient nguyên thủy nhất. Nghiên cứu Sobel giúp nhóm hiểu sâu chính nền tảng toán học mà dự án đang dùng, đồng thời mở ra khả năng nâng cấp thật cho dự án.')
p('Mục tiêu của báo cáo:', bold=True, space_after=3)
bullet('Trình bày hệ thống cơ sở lý thuyết chung của học phần: các phép biến đổi điểm, lọc không gian, cân bằng histogram và cắt bit-plane (Chương 1).')
bullet('Đào sâu bộ lọc Sobel: cơ sở toán học của gradient, cấu trúc hai kernel, độ lớn và hướng cạnh, ví dụ tính tay và so sánh với các toán tử khác (Chương 2).')
bullet('Giới thiệu dự án VisionCleanse và phân tích các giới hạn hiện tại của dự án dưới góc nhìn xử lý ảnh (Chương 3).')
bullet('Thiết kế và tích hợp Sobel vào VisionCleanse thành "vòng 2.5" — lớp xác minh bằng dấu vân tay cạnh, kèm mã nguồn và kiểm thử đầy đủ (Chương 4).')
bullet('Thực nghiệm đo lường định lượng: so sánh khoảng cách Hamming của pHash, dHash và edge_hash (Sobel) trên 16 biến thể ảnh, rút ra kết luận và giới hạn trung thực (Chương 5).')
p('Phạm vi: báo cáo tập trung vào ảnh xám (grayscale) và các phép toán trên miền không gian; phần thực nghiệm dùng ảnh kiểm thử tổng hợp do chính dự án sinh ra, chạy bằng Python với hai thư viện numpy và Pillow — không dùng OpenCV — để giữ đúng triết lý ít phụ thuộc của dự án.')
chapter_break()

# =====================================================================
# CHUONG 1
# =====================================================================
p('Chương 1', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('CƠ SỞ LÝ THUYẾT CHUNG VỀ XỬ LÝ ẢNH VÀ LỌC KHÔNG GIAN', style='Heading 1')
p('1.1. Ảnh số và biểu diễn ảnh', style='Heading 2')
p('Ảnh số là hàm hai biến rời rạc f(x, y), trong đó x, y là tọa độ không gian và giá trị f tại mỗi điểm (pixel) biểu diễn độ sáng (ảnh xám) hoặc bộ ba kênh màu đỏ, lục, lam (ảnh màu RGB). Ảnh xám 8 bit có mức xám từ 0 (đen) đến 255 (trắng). Mọi phép xử lý trong báo cáo này đều thao tác trên ma trận số nguyên này, chủ yếu sau khi đã chuyển ảnh màu về ảnh xám bằng tổ hợp tuyến tính của ba kênh màu.')
p('Các phép biến đổi ảnh được chia thành ba nhóm lớn: (i) biến đổi điểm — giá trị pixel đầu ra chỉ phụ thuộc vào chính pixel đó; (ii) lọc không gian — giá trị đầu ra phụ thuộc vào một lân cận của pixel; (iii) biến đổi miền tần số — thao tác trên phổ Fourier của ảnh. Chương này lần lượt điểm qua các kỹ thuật tiêu biểu của học phần trước khi đi sâu vào bộ lọc Sobel ở Chương 2.')
p('1.2. Các phép biến đổi điểm (biến đổi mức xám)', style='Heading 2')
p('Biến đổi điểm có dạng s = T(r), trong đó r là mức xám đầu vào và s là mức xám đầu ra. Bốn phép biến đổi cơ bản gồm:', space_after=3)
bullet('phép biến đổi âm bản (Digital Negative): s = (L − 1) − r, đảo ngược mức xám; hữu ích khi vùng quan tâm có tông sáng chiếm ưu thế trên nền tối, ví dụ ảnh X-quang. Đây cũng là phép biến đổi sẽ xuất hiện lại trong Chương 5 với vai trò "kẻ phá hoại" các hàm băm cảm nhận.', bold_prefix='Biến đổi âm bản: ')
bullet('phép biến đổi logarit s = c · log(1 + r) nén dải động lớn, làm rõ chi tiết ở vùng tối; phép nghịch đảo (exp) có tác dụng ngược lại.', bold_prefix='Biến đổi Logarit: ')
bullet('phép biến đổi lũy thừa s = c · r^γ; với γ < 1 ảnh sáng lên và rõ vùng tối, với γ > 1 ảnh tối đi; đây là cơ sở của hiệu chỉnh gamma trên mọi màn hình.', bold_prefix='Biến đổi Power-Law (Gamma): ')
bullet('hàm biến đổi được định nghĩa từng đoạn tuyến tính, cho phép kéo giãn tương phản có chọn lọc, cắt mức xám (gray-level slicing) và cắt mặt phẳng bit.', bold_prefix='Biến đổi Piecewise-Linear: ')
p('Điểm chung quan trọng cho các chương sau: cả bốn phép biến đổi trên đều là hàm đơn điệu của mức xám (trừ âm bản là đơn điệu giảm). Chúng thay đổi tông màu của ảnh nhưng không làm thay đổi vị trí các biên — nhận xét này là chìa khóa giải thích vì sao dấu vân tay cạnh Sobel bền vững trước chúng (Chương 5).')
p('1.3. Lọc không gian (Spatial Filtering)', style='Heading 2')
p('Lọc không gian thực hiện phép nhân chập (convolution) giữa ảnh với một kernel (mặt nạ lọc) kích thước thường là 3×3 hoặc 5×5: kernel trượt qua từng pixel, giá trị đầu ra là tổng có trọng số của các pixel trong lân cận. Tùy hệ số của kernel, lọc không gian chia thành hai họ lớn: lọc làm trơn (low-pass) và lọc làm sắc nét / phát hiện cạnh (high-pass).')
table(['Bộ lọc', 'Kernel / cách tính', 'Tác dụng chính', 'Nhược điểm'],
      [['Trung bình (Mean)', 'Mọi hệ số bằng 1/9 (kernel 3×3)', 'Làm trơn, giảm nhiễu cộng', 'Làm mờ cả cạnh'],
       ['Gaussian', 'Hệ số theo phân bố Gauss, trọng tâm lớn nhất', 'Làm trơn tự nhiên, tiền xử lý chuẩn cho phát hiện cạnh', 'Vẫn làm mờ cạnh nếu bán kính lớn'],
       ['Trung vị (Median)', 'Lấy trung vị của lân cận, không có kernel tuyến tính', 'Khử nhiễu muối tiêu rất tốt', 'Tốn tính toán, không phải phép chập tuyến tính'],
       ['Laplacian', 'Đạo hàm bậc hai, kernel có tâm âm/dương đối xứng', 'Làm sắc nét, phát hiện vùng thay đổi nhanh', 'Rất nhạy nhiễu, không cho hướng cạnh'],
       ['Sobel / Prewitt', 'Hai kernel đạo hàm bậc nhất theo hai trục', 'Phát hiện cạnh kèm hướng', 'Cạnh dày, cần hậu xử lý ngưỡng']],
      widths=[3.0, 4.6, 4.4, 3.5])
caption('Bảng 1.1. Các phép lọc không gian phổ biến trong học phần.')
p('Ba bộ lọc làm trơn đầu tiên (trung bình, Gaussian, trung vị) thuộc nhóm lọc thông thấp; Laplacian, Sobel, Prewitt thuộc nhóm lọc thông cao dựa trên đạo hàm. Báo cáo tập trung vào họ đạo hàm vì chúng gắn trực tiếp với dự án VisionCleanse.')
p('1.4. Histogram và cân bằng histogram', style='Heading 2')
p('Histogram của ảnh xám là phân bố số pixel theo từng mức xám. Cân bằng histogram (Histogram Equalization) biến đổi mức xám dựa trên hàm phân phối tích lũy (CDF) để histogram đầu ra xấp xỉ đều, qua đó kéo giãn tương phản toàn cục. Kỹ thuật này minh họa rõ nguyên tắc "biến đổi dựa trên thống kê toàn ảnh" — cùng một ý tưởng thống kê sẽ gặp lại ở Chương 4, khi dự án dùng trung vị của một ma trận hệ số làm ngưỡng nhị phân hóa.')
p('1.5. Cắt mặt phẳng bit (Bit-plane Slicing)', style='Heading 2')
p('Mỗi pixel 8 bit được tách thành 8 mặt phẳng bit, từ bit cao nhất (MSB, chứa phần lớn cấu trúc thị giác) đến bit thấp nhất (LSB, gần như nhiễu). Cắt mặt phẳng bit cho thấy thông tin ảnh phân bố không đều theo bit — tiền đề trực quan cho các hàm băm cảm nhận ở Chương 3, nơi ảnh được rút gọn thành đúng 64 bit dấu vân tay mà vẫn giữ được cấu trúc chính.')
p('1.6. Phát hiện cạnh và vai trò của gradient', style='Heading 2')
p('Cạnh (edge) là tập hợp các pixel tại đó mức xám thay đổi đột ngột — thường là biên của vật thể, ranh giới vùng vật liệu hoặc đường nét. Vì đạo hàm đo tốc độ thay đổi, phát hiện cạnh đồng nghĩa với việc tìm các điểm có đạo hàm lớn. Gradient của ảnh tại một điểm là vector gồm hai thành phần đạo hàm riêng theo x và theo y; độ lớn của gradient cho biết "mức độ cạnh", còn hướng của gradient cho biết phương vuông góc với cạnh. Chương 2 trình bày cách bộ lọc Sobel xấp xỉ gradient này bằng hai phép nhân chập rời rạc.')
chapter_break()

# =====================================================================
# CHUONG 2
# =====================================================================
p('Chương 2', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('BỘ LỌC SOBEL — LÝ THUYẾT CHUYÊN SÂU', style='Heading 1')
p('2.1. Nguồn gốc và ý tưởng', style='Heading 2')
p('Toán tử Sobel được Irwin Sobel và Gary Feldman giới thiệu năm 1968 tại Phòng thí nghiệm Trí tuệ nhân tạo Stanford, trong bài trình bày "A 3×3 Isotropic Gradient Operator for Image Processing". Ý tưởng cốt lõi: thay vì tính đạo hàm bằng hiệu hai điểm (rất nhạy nhiễu), hãy kết hợp phép lấy đạo hàm theo một trục với phép làm trơn theo trục còn lại ngay trong cùng một kernel 3×3. Nhờ vậy Sobel vừa phát hiện cạnh, vừa tự khử một phần nhiễu — và cho ra phép đo gradient đẳng hướng (isotropic) tốt trong các toán tử 3×3.')
p('2.2. Từ đạo hàm liên tục đến hiệu rời rạc', style='Heading 2')
p('Với ảnh liên tục f(x, y), gradient là vector ∇f = (∂f/∂x, ∂f/∂y). Trên ảnh số, đạo hàm được xấp xỉ bằng hiệu hữu hạn. Xấp xỉ thô nhất theo trục x là f(x, y+1) − f(x, y), tương ứng kernel 1×2 là [−1, +1] — đáng chú ý, đây chính là phép toán mà thuật toán dHash của VisionCleanse thực hiện ở quy mô toàn ảnh (Chương 3). Sobel mở rộng ý tưởng này lên kernel 3×3 có trọng số.')
p('2.3. Hai kernel Sobel và cách phân tích cấu trúc', style='Heading 2')
p('Kernel theo trục x (nhân chập cho ra thành phần Gx, nhạy với cạnh dọc):', space_after=3)
code_block('Gx = [ -1   0   +1 ]\n     [ -2   0   +2 ]\n     [ -1   0   +1 ]')
p('Kernel theo trục y (cho ra thành phần Gy, nhạy với cạnh ngang):', space_after=3)
code_block('Gy = [ -1  -2   -1 ]\n     [  0   0    0 ]\n     [ +1  +2   +1 ]')
p('Mỗi kernel Sobel phân tích được thành tích của một vector làm trơn và một vector đạo hàm. Cụ thể, Gx = [1, 2, 1]ᵀ × [−1, 0, +1]: cột [1, 2, 1] là bộ lọc làm trơn (dạng rời rạc của Gaussian) theo trục y, còn hàng [−1, 0, +1] là đạo hàm trung tâm theo trục x. Tính tách được (separability) này vừa giải thích khả năng chống nhiễu của Sobel, vừa cho phép cài đặt nhanh bằng hai phép chập 1 chiều.')
callout('Nhận xét quan trọng. ', 'Hệ số 2 ở hàng/cột giữa là điểm khác biệt duy nhất giữa Sobel và Prewitt (Prewitt dùng toàn hệ số 1). Trọng số lớn hơn cho pixel trung tâm khiến đáp ứng của Sobel đẳng hướng hơn và ít nhạy nhiễu hơn Prewitt, với chi phí tính toán gần như không đổi.')
p('2.4. Độ lớn và hướng của gradient', style='Heading 2')
p('Sau khi nhân chập, mỗi pixel có hai giá trị Gx và Gy. Độ lớn gradient được tính theo công thức Euclid G = √(Gx² + Gy²); trong thực hành thường dùng xấp xỉ G ≈ |Gx| + |Gy| để tránh phép căn. Hướng của gradient là θ = arctan(Gy / Gx), cho biết hướng thay đổi mức xám mạnh nhất — cạnh tại điểm đó vuông góc với hướng này. Ảnh độ lớn gradient là "bản đồ cạnh": vùng phẳng gần như đen, biên vật thể sáng lên.')
figure('fig_sobel_4up.png', 'Hình 2.1. Kết quả lọc Sobel trên ảnh kiểm thử tổng hợp của dự án: ảnh gốc, thành phần Gx (cạnh dọc), thành phần Gy (cạnh ngang) và độ lớn gradient G = √(Gx² + Gy²).', width_cm=15.0)
p('2.5. Ví dụ tính tay', style='Heading 2')
p('Xét một lân cận 3×3 chứa một cạnh dọc lý tưởng: cột trái và cột giữa có mức xám 100, cột phải có mức xám 200.', space_after=3)
code_block('Lan can:  [ 100  100  200 ]\n          [ 100  100  200 ]\n          [ 100  100  200 ]')
p('Áp kernel Gx: (−1·100 + 0·100 + 1·200) + (−2·100 + 0·100 + 2·200) + (−1·100 + 0·100 + 1·200) = 100 + 200 + 100 = 400. Áp kernel Gy: hàng trên và hàng dưới của lân cận giống hệt nhau nên các số hạng triệt tiêu, Gy = 0. Độ lớn G = √(400² + 0²) = 400 — một giá trị lớn, đúng kỳ vọng tại vị trí cạnh; hướng θ = arctan(0/400) = 0°, gradient chỉ theo trục x, tức cạnh chạy dọc. Ngược lại, nếu lân cận hoàn toàn phẳng (mọi pixel bằng 100), cả Gx và Gy đều bằng 0 — vùng phẳng không tạo đáp ứng.')
p('2.6. Ngưỡng cạnh và hậu xử lý', style='Heading 2')
p('Bản đồ độ lớn gradient là ảnh xám; để thu được bản đồ cạnh nhị phân cần chọn một ngưỡng T: pixel có G ≥ T được coi là điểm cạnh. Ngưỡng quá thấp sinh nhiều cạnh giả do nhiễu; ngưỡng quá cao làm đứt các cạnh yếu. Các kỹ thuật chọn ngưỡng gồm ngưỡng cố định theo kinh nghiệm, ngưỡng theo thống kê (ví dụ trung vị hoặc phân vị của phân bố G), và ngưỡng thích nghi kiểu Otsu. Thuật toán Canny — chuẩn mực của phát hiện cạnh — dùng Sobel ở bước tính gradient, sau đó áp dụng triệt cạnh không cực đại (non-maximum suppression) và ngưỡng trễ (hysteresis) để làm mỏng và nối cạnh.')
p('2.7. So sánh với các toán tử phát hiện cạnh khác', style='Heading 2')
table(['Tiêu chí', 'Roberts', 'Prewitt', 'Sobel', 'Laplacian'],
      [['Kích thước kernel', '2×2 (chéo)', '3×3', '3×3', '3×3'],
       ['Bậc đạo hàm', 'Bậc nhất', 'Bậc nhất', 'Bậc nhất', 'Bậc hai'],
       ['Trọng số làm trơn', 'Không', 'Đồng đều (1)', 'Có (2 ở giữa)', 'Không'],
       ['Cho hướng cạnh', 'Có (chéo)', 'Có', 'Có', 'Không'],
       ['Độ nhạy nhiễu', 'Rất cao', 'Trung bình', 'Thấp nhất trong nhóm bậc nhất 3×3', 'Rất cao'],
       ['Ứng dụng điển hình', 'Ảnh ít nhiễu, xử lý nhanh', 'Giảng dạy, minh họa', 'Tiền xử lý cho Canny, đặc trưng cạnh', 'Làm sắc nét, phát hiện đốm']],
      widths=[3.2, 2.8, 2.8, 3.4, 3.3])
caption('Bảng 2.1. So sánh các toán tử phát hiện cạnh phổ biến.')
p('2.8. Ưu điểm và hạn chế', style='Heading 2')
bullet('Cài đặt đơn giản, tính tách được nên chạy nhanh; chỉ cần hai phép nhân chập 3×3.', bold_prefix='Ưu điểm: ')
bullet('Đáp ứng đẳng hướng tốt trong các toán tử 3×3; có sẵn thành phần làm trơn nên bền nhiễu hơn Prewitt và Roberts.', bold_prefix='')
bullet('Cho đồng thời độ lớn và hướng cạnh — đủ thông tin cho các bước xử lý tiếp theo.', bold_prefix='')
bullet('Cạnh đầu ra dày (nhiều pixel cùng có đáp ứng cao quanh một cạnh thật), cần bước làm mỏng cạnh.', bold_prefix='Hạn chế: ')
bullet('Vẫn là toán tử tuyến tính cục bộ: nhạy với nhiễu mạnh và không hiểu ngữ nghĩa — cạnh do bóng đổ hay họa tiết cũng được phát hiện như cạnh vật thể.', bold_prefix='')
bullet('Độ lớn gradient phụ thuộc vào độ tương phản tuyệt đối: cùng một cấu trúc nhưng tương phản thấp sẽ cho đáp ứng thấp (tính chất này quay lại trong phân tích thực nghiệm ở Chương 5).', bold_prefix='')
p('2.9. Ứng dụng của bộ lọc Sobel', style='Heading 2')
p('Sobel xuất hiện trong tiền xử lý của nhận dạng biển số, phát hiện làn đường, kiểm tra lỗi bề mặt công nghiệp, phân tích ảnh y tế (nêu biên tổn thương), và là bước tính gradient mặc định trong thuật toán Canny cũng như trong mô tả đặc trưng HOG (Histogram of Oriented Gradients) — nền tảng của phát hiện người đi bộ cổ điển. Chương 4 trình bày một ứng dụng ít gặp hơn nhưng rất thực tế: dùng bản đồ cạnh Sobel để tạo dấu vân tay cấu trúc cho bài toán phát hiện ảnh trùng lặp.')
chapter_break()

# =====================================================================
# CHUONG 3
# =====================================================================
p('Chương 3', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('GIỚI THIỆU DỰ ÁN VISIONCLEANSE', style='Heading 1')
p('3.1. Bài toán: tập dữ liệu bẩn và rò rỉ dữ liệu', style='Heading 2')
p('VisionCleanse (github.com/MinhTriTM/vision-cleanse) là công cụ dòng lệnh bằng Python do nhóm phát triển, dùng để làm sạch tập dữ liệu thị giác máy tính trước khi huấn luyện mô hình. Hai vấn đề công cụ giải quyết là: (i) ảnh trùng và gần trùng (near-duplicate) nằm rải rác trong tập dữ liệu do thu thập từ nhiều nguồn; (ii) rò rỉ dữ liệu (data leakage) — cùng một ảnh (hoặc bản sao đã biến đổi nhẹ) xuất hiện ở cả tập huấn luyện và tập kiểm tra, khiến điểm đánh giá mô hình cao giả tạo. Công cụ quét các thư mục train/val/test, nhóm các ảnh trùng, cách ly (quarantine) bản sao thừa theo nguyên tắc ưu tiên tập kiểm tra, kiểm tra "sức khỏe" tập dữ liệu (ảnh hỏng, ảnh trơn, gán nhãn lệch) và xuất báo cáo HTML có thể kiểm chứng lại.')
p('3.2. Kiến trúc các vòng phát hiện', style='Heading 2')
p('VisionCleanse phát hiện trùng lặp theo từng "vòng" (ring) với độ mềm dẻo tăng dần:', space_after=3)
bullet('băm mật mã (MD5/SHA-256) trên nội dung tệp — chỉ bắt được các bản sao giống hệt từng byte.', bold_prefix='Vòng 1 — trùng chính xác: ')
bullet('băm cảm nhận pHash và dHash — bắt được ảnh đã thay đổi kích thước, nén lại hoặc đổi định dạng. Đây là vòng mà báo cáo này phân tích và mở rộng.', bold_prefix='Vòng 2 — gần trùng: ')
bullet('theo lộ trình của dự án (ROADMAP-1.0): xác minh hình học bằng đặc trưng cục bộ (SIFT + RANSAC) để xử lý crop sâu, xoay, lật và ảnh ghép. Vòng này nặng và chưa triển khai.', bold_prefix='Vòng 4 (lộ trình) — trùng từng phần: ')
p('Giữa vòng 2 và vòng 4 tồn tại một khoảng trống: các biến đổi tông màu mạnh (đổi sáng, tương phản, gamma, âm bản) và các cặp "bố cục giống nhưng khác ảnh" gây báo giả. Khoảng trống đó chính là nơi vòng 2.5 dùng Sobel được đề xuất ở Chương 4.')
p('3.3. pHash và dHash dưới góc nhìn xử lý ảnh', style='Heading 2')
p('Cả hai hàm băm cảm nhận của dự án đều bắt đầu bằng cùng một bước tiền xử lý: chuyển ảnh về ảnh xám và thu nhỏ về kích thước cố định bằng nội suy Lanczos (hàm _grayscale_pixels trong extractors.py). Sau đó:', space_after=3)
bullet('ảnh xám 32×32 được biến đổi cosin rời rạc (DCT-II), giữ lại khối hệ số tần số thấp 8×8 ở góc trên-trái, rồi nhị phân hóa bằng cách so từng hệ số với trung vị của khối: hệ số lớn hơn trung vị thành bit 1, ngược lại thành bit 0. Kết quả là dấu vân tay 64 bit mô tả cấu trúc tần số thấp của ảnh.', bold_prefix='pHash: ')
bullet('ảnh xám được thu về 9×8; mỗi pixel được so với pixel kề phải của nó — tức dấu của hiệu f(x, y+1) − f(x, y) — tạo thành 64 bit. Nói bằng ngôn ngữ của Chương 1 và 2: dHash là dấu của gradient ngang tính bằng kernel [−1, +1], không có làm trơn, không có thành phần dọc.', bold_prefix='dHash: ')
p('Hai ảnh được coi là gần trùng khi khoảng cách Hamming giữa hai dấu vân tay (số bit khác nhau) không vượt quá một ngưỡng, mặc định là 10 trên 64 bit. Tham số này phơi bày qua giao diện dòng lệnh: --phash-threshold và --dhash-threshold.')
p('3.4. Các giới hạn hiện tại nhìn từ lý thuyết xử lý ảnh', style='Heading 2')
p('README của dự án tự ghi rõ: "Chưa bắt crop sâu, xoay, lật, đổi màu mạnh". Phân tích theo lý thuyết đã học cho thấy gốc rễ của từng giới hạn:', space_after=3)
bullet('cả pHash và dHash đều mã hóa tông màu (trực tiếp qua hệ số DCT, hoặc qua dấu hiệu độ sáng kề). Phép âm bản s = 255 − r đảo ngược mọi quan hệ "lớn hơn/nhỏ hơn" trong ảnh: dấu gradient của dHash bị lật toàn bộ, hệ số DCT của pHash đổi dấu — hai dấu vân tay trở nên gần như đối nghịch dù ảnh chỉ khác tông.', bold_prefix='Đổi tông mạnh: ')
bullet('matchers.py của dự án đã ghi nhận hiện tượng các ảnh khác nhau nhưng cùng bố cục (ví dụ nhiều ảnh chụp cùng một sân khấu) có dấu vân tay đủ gần để bị nhóm nhầm khi chỉ dùng một hàm băm. Cần thêm một tín hiệu độc lập để xác minh.', bold_prefix='Báo giả do bố cục giống: ')
bullet('bộ kiểm tra sức khỏe hiện tại chỉ phát hiện ảnh trơn hoàn toàn (độ lệch chuẩn của ảnh xám nhỏ hơn 1.0). Ảnh bị mờ do mất nét vẫn "qua cửa" dù gần như vô dụng cho huấn luyện.', bold_prefix='Chưa phát hiện ảnh mờ: ')
p('3.5. Vì sao Sobel là mảnh ghép phù hợp', style='Heading 2')
p('Bản đồ cạnh Sobel mã hóa vị trí thay đổi độ sáng thay vì chính độ sáng. Các phép biến đổi điểm đơn điệu (sáng, tương phản, gamma) không dời vị trí cạnh; phép âm bản đổi chiều gradient nhưng giữ nguyên độ lớn gradient. Do đó một dấu vân tay xây trên độ lớn gradient Sobel hứa hẹn bất biến với đúng nhóm biến đổi đang làm khó vòng 2 — đồng thời vẫn phân biệt được các ảnh khác cấu trúc. Về mặt cài đặt, Sobel chỉ cần numpy và Pillow, khớp triết lý "không thêm phụ thuộc nặng" của dự án (dự án thậm chí tự cài đặt DCT cho pHash thay vì dùng thư viện imagehash).')
chapter_break()

# =====================================================================
# CHUONG 4
# =====================================================================
p('Chương 4', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('TÍCH HỢP BỘ LỌC SOBEL VÀO VISIONCLEANSE (VÒNG 2.5)', style='Heading 1')
p('4.1. Thiết kế tổng thể', style='Heading 2')
p('Vòng 2.5 được thiết kế theo ba nguyên tắc: (1) opt-in — mặc định tắt, hành vi cũ của công cụ không thay đổi; (2) Sobel chỉ đóng vai trò lớp xác minh, không bao giờ tự đứng ra nhóm ảnh một mình; (3) khi Sobel không có thông tin (ảnh không có cấu trúc cạnh), quyền quyết định trả lại hoàn toàn cho pHash/dHash. Ba thành phần mới được thêm vào mã nguồn hiện có:', space_after=3)
table(['Tệp', 'Thành phần mới', 'Vai trò'],
      [['extractors.py', 'sobel_magnitude(), edge_hash(), edge_energy(), sobel_magnitude_image()', 'Trích xuất đặc trưng cạnh Sobel và dấu vân tay cạnh 64 bit'],
       ['matchers.py', 'Tham số edge_threshold trong group_duplicates()', 'Luật xác minh hai chiều: cứu cặp trượt và phủ quyết cặp báo giả'],
       ['core.py', 'Tham số sobel_verify, sobel_threshold', 'Tính edge_hash khi được bật, ghi vào hồ sơ ảnh và báo cáo'],
       ['cli.py', 'Cờ --sobel-verify, --sobel-threshold', 'Điều khiển từ dòng lệnh'],
       ['tests/test_sobel.py', '14 kiểm thử đơn vị', 'Khóa chặt hành vi, gồm cả các giới hạn trung thực']],
      widths=[3.0, 5.6, 6.4])
caption('Bảng 4.1. Các thành phần mã nguồn của vòng 2.5.')
p('4.2. Đào sâu tầng trích xuất đặc trưng (extractors.py)', style='Heading 2')
p('4.2.1. Phép nhân chập 3×3 bằng cộng dịch chuyển', style='Heading 3')
p('Thay vì vòng lặp trên từng pixel (chậm trong Python), phép nhân chập được cài đặt bằng chín phép cộng ma trận đã dịch chuyển trên bản sao ảnh đã đệm viền (edge padding). Cách cài đặt này vừa vector hóa hoàn toàn bằng numpy, vừa giữ mã nguồn ngắn và dễ kiểm chứng:', space_after=3)
code_block('''_SOBEL_GX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
_SOBEL_GY = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)

def _conv3x3(img, kernel):
    """3x3 convolution by shifted adds (edge-padded, no per-pixel loop)."""
    out = np.zeros_like(img)
    p = np.pad(img, 1, mode="edge")
    h, w = img.shape
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            out += kernel[i + 1, j + 1] * p[1 + i:1 + i + h, 1 + j:1 + j + w]
    return out''', 'Mã nguồn 4.1. Hai kernel Sobel và phép nhân chập vector hóa.')
p('4.2.2. Độ lớn gradient và dấu vân tay cạnh edge_hash', style='Heading 3')
p('Hàm sobel_magnitude() tái sử dụng đúng bước tiền xử lý của pHash/dHash (ảnh xám thu nhỏ 32×32), sau đó tính G = √(Gx² + Gy²) cho mọi pixel. Từ bản đồ độ lớn này, edge_hash() rút ra dấu vân tay 64 bit bằng cùng một "thủ thuật ngưỡng trung vị" mà pHash dùng cho hệ số DCT — nhưng áp lên cạnh thay vì tần số: bản đồ 32×32 được chia thành lưới 8×8 khối, lấy trung bình từng khối, rồi so với trung vị của 64 giá trị khối:', space_after=3)
code_block('''def edge_hash(path, hash_size=8):
    mag = sobel_magnitude(path, (32, 32))
    block = 32 // hash_size
    small = mag.reshape(hash_size, block, hash_size, block).mean(axis=(1, 3))
    return _bits_to_int(small > np.median(small))''', 'Mã nguồn 4.2. Hàm edge_hash — dấu vân tay cấu trúc cạnh 64 bit.')
p('Việc cố ý dùng lại ngưỡng trung vị không chỉ tiết kiệm mã: nó khiến edge_hash có cùng "ngữ nghĩa thống kê" với pHash (mỗi dấu vân tay luôn có khoảng một nửa số bit bằng 1), nên cùng một ngưỡng Hamming mặc định 10 có thể dùng chung cho cả ba hàm băm.')
figure('fig_edge_invert.png', 'Hình 4.1. Bản đồ cạnh Sobel của ảnh gốc (c) và của ảnh âm bản (d) giống hệt nhau, dù hai ảnh gốc (a) và (b) đối nghịch hoàn toàn về tông màu. Đây là nền tảng trực quan của tính bất biến tông màu.', width_cm=13.0)
p('4.2.3. Năng lượng cạnh edge_energy — tín hiệu phát hiện ảnh mờ', style='Heading 3')
p('Hàm edge_energy() trả về giá trị trung bình của độ lớn gradient Sobel, đo trên ảnh xám 128×128. Ảnh sắc nét, giàu cấu trúc cho giá trị cao; ảnh mờ cho giá trị thấp vì làm mờ Gaussian triệt tiêu chính các thành phần thay đổi nhanh mà Sobel đo. Chi tiết đo ở 128×128 thay vì 32×32 là một quyết định có đo lường: ở 32×32, bước thu nhỏ đã tự làm mờ ảnh nên một lần làm mờ Gaussian bán kính 3 chỉ kéo năng lượng xuống 0,93 lần; ở 128×128, cùng phép làm mờ kéo năng lượng xuống 0,47 lần — đủ rõ để dùng làm ngưỡng cảnh báo trong bộ kiểm tra sức khỏe.')
p('4.2.4. Hàm sobel_magnitude_image — phục vụ minh họa và báo cáo', style='Heading 3')
p('Hàm này xuất bản đồ cạnh ở độ phân giải đầy đủ, chuẩn hóa về dải 0–255, dùng để sinh hình minh họa cho báo cáo và slide (Hình 2.1) và có thể mở rộng để đính kèm vào báo cáo HTML của công cụ, giúp người dùng nhìn thấy vì sao hai ảnh bị kết luận là trùng.')
p('4.3. Đào sâu tầng đối sánh (matchers.py): luật xác minh hai chiều', style='Heading 2')
p('Hàm group_duplicates() nhận thêm tham số edge_threshold (mặc định None — tắt). Khi được bật, với mỗi cặp ảnh ứng viên, luật quyết định thay đổi như sau:', space_after=3)
bullet('nếu cả hai ảnh đều có edge_hash và cả hai đều khác 0, khoảng cách Hamming của edge_hash là quyết định cuối cùng: nhỏ hơn hoặc bằng ngưỡng thì nhóm, lớn hơn thì không nhóm — bất kể pHash/dHash nói gì.', bold_prefix='Cặp có đủ thông tin cạnh: ')
bullet('nếu một trong hai edge_hash bằng 0 hoặc không tồn tại, luật cũ của pHash/dHash được áp dụng nguyên vẹn.', bold_prefix='Cặp thiếu thông tin cạnh: ')
bullet('các cặp trùng chính xác theo MD5 không bao giờ bị ảnh hưởng.', bold_prefix='Ngoại lệ: ')
p('Luật này tạo ra hai tác dụng ngược chiều nhưng cùng có lợi. Chiều thứ nhất là cứu (rescue): cặp ảnh trùng đã bị đổi tông mạnh mà pHash/dHash bỏ qua (khoảng cách vượt ngưỡng) sẽ được nhóm lại nhờ edge_hash khớp. Chiều thứ hai là phủ quyết (veto): cặp ảnh khác nhau có bố cục giống nhau bị pHash/dHash nhóm nhầm sẽ bị tách ra vì cấu trúc cạnh khác nhau. Đây là lý do vòng 2.5 được mô tả là "lớp xác minh" chứ không phải một hàm băm độc lập nữa.')
callout('Vì sao edge_hash bằng 0 phải bị loại khỏi quyền quyết định? ', 'Giá trị 0 ở đây không có nghĩa là "rất ít cạnh" mà là "bản đồ cạnh đồng đều đến mức mọi khối đều không vượt trung vị" — trường hợp này xảy ra với ảnh gradient tuyến tính hoặc bàn cờ đều, vốn không chứa thông tin cấu trúc phân biệt được. Nếu để giá trị 0 tham gia quyết định, mọi ảnh dạng này sẽ bị coi là trùng nhau. Thiết kế chọn cách trung thực: không có thông tin thì không phán quyết, giống như cách dự án đã xử lý ảnh trơn (blank) ở vòng 2.')
p('4.4. Đào sâu tầng điều phối và giao diện dòng lệnh (core.py, cli.py)', style='Heading 2')
p('Trong core.py, hàm clean() chỉ tính edge_hash cho từng ảnh khi cờ sobel_verify được bật (tránh tốn tính toán khi không dùng), lưu vào hồ sơ ảnh dưới khóa "edge_hash" và truyền ngưỡng xuống tầng đối sánh; báo cáo đầu ra ghi lại hai trường sobel_verify và sobel_threshold để mọi kết luận đều truy vết được cấu hình đã sinh ra nó. Phía người dùng, cách bật vòng 2.5 chỉ là thêm một cờ:', space_after=3)
code_block('visioncleanse ./dataset --sobel-verify --sobel-threshold 10', 'Mã nguồn 4.3. Cách chạy VisionCleanse với vòng xác minh Sobel được bật.')
p('4.5. Kiểm thử', style='Heading 2')
p('Tệp tests/test_sobel.py bổ sung 14 kiểm thử đơn vị, trong đó quan trọng nhất là: (1) ảnh âm bản giữ nguyên edge_hash (khoảng cách 0) trong khi pHash lệch 62 bit và dHash lệch 64 bit; (2) giảm tương phản xuống 0,3 và làm mờ Gaussian bán kính 2 vẫn giữ edge_hash trong ngưỡng 10; (3) một ảnh khác cấu trúc có edge_hash cách xa ít nhất 20 bit; (4) ảnh gradient tuyến tính và bàn cờ đều cho edge_hash bằng 0 và không bao giờ bị phủ quyết oan; (5) làm mờ Gaussian bán kính 3 kéo edge_energy xuống còn khoảng 0,47 lần. Toàn bộ bộ kiểm thử của dự án sau khi tích hợp gồm 88 kiểm thử đạt, 7 kiểm thử bỏ qua theo điều kiện môi trường — không có kiểm thử cũ nào bị phá vỡ, đúng cam kết opt-in của thiết kế.')
chapter_break()

# =====================================================================
# CHUONG 5
# =====================================================================
p('Chương 5', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('THỰC NGHIỆM VÀ ĐÁNH GIÁ', style='Heading 1')
p('5.1. Thiết lập thực nghiệm', style='Heading 2')
p('Ảnh gốc là ảnh kiểm thử tổng hợp do chính bộ kiểm thử của dự án sinh ra (hàm photo_like: nền nhiễu nhẹ với các hình khối và đường tròn màu — có cấu trúc cạnh rõ ràng, gần với ảnh chụp thật hơn là ảnh trơn). Từ ảnh gốc, nhóm tạo 15 biến thể mô phỏng các biến đổi thường gặp khi một ảnh bị sao chép và chỉnh sửa: thay đổi kích thước, nén JPEG, tăng/giảm sáng, thay đổi tương phản, hiệu chỉnh gamma 0,5 và 2,0, âm bản, làm mờ Gaussian, làm nét, cắt xén (crop) 10% và 25% mỗi cạnh, lật ngang, cộng nhiễu Gaussian; cộng thêm một ảnh hoàn toàn khác (hạt giống ngẫu nhiên khác) làm đối chứng âm. Với mỗi biến thể, nhóm đo khoảng cách Hamming tới ảnh gốc của ba dấu vân tay pHash, dHash, edge_hash và tỉ lệ năng lượng cạnh so với ảnh gốc. Ngưỡng kết luận trùng là 10 bit — đúng mặc định của dự án. Toàn bộ thí nghiệm chạy bằng mã nguồn thật của dự án trên nhánh vision-cleanse-BaiTapLonImageProcessing.')
rows = []
for r in RESULTS:
    rows.append([r['variant'], r['phash'], r['dhash'], r['edge'], r['energy_ratio']])
table(['Biến thể', 'pHash', 'dHash', 'edge_hash (Sobel)', 'Tỉ lệ năng lượng cạnh'], rows,
      widths=[6.2, 1.8, 1.8, 3.2, 3.0])
caption('Bảng 5.1. Khoảng cách Hamming (bit, tối đa 64) của ba dấu vân tay so với ảnh gốc và tỉ lệ edge_energy. Giá trị ≤ 10 được coi là "trùng" theo ngưỡng mặc định.')
figure('fig_hamming.png', 'Hình 5.1. Khoảng cách Hamming của pHash, dHash và edge_hash trên các biến thể tiêu biểu. Đường đứt nét đỏ là ngưỡng trùng mặc định (10 bit).', width_cm=15.0)
p('5.2. Phân tích kết quả theo nhóm biến đổi', style='Heading 2')
p('5.2.1. Nhóm biến đổi tông màu — nơi Sobel thắng tuyệt đối ở trường hợp cực đoan', style='Heading 3')
p('Với các biến đổi tông màu vừa phải (tăng sáng 1,5 lần, giảm sáng 0,5 lần, tương phản 0,3 và 1,8, gamma 0,5 và 2,0), cả ba dấu vân tay đều nằm trong ngưỡng (khoảng cách từ 0 đến 8 bit) — các hàm băm hiện tại vốn đã bền với nhóm này. Nhưng ở biến đổi cực đoan nhất là âm bản, kết quả phân hóa hoàn toàn: pHash lệch 62/64 bit và dHash lệch 64/64 bit — tức hai dấu vân tay bị phá hủy hoàn toàn, cặp ảnh trùng chắc chắn bị bỏ qua — trong khi edge_hash lệch đúng 0 bit. Kết quả này khớp chính xác với dự đoán lý thuyết ở mục 3.5: âm bản đảo dấu mọi quan hệ độ sáng nhưng giữ nguyên độ lớn gradient, và Hình 4.1 cho thấy trực quan hai bản đồ cạnh trùng khớp hoàn toàn. Đây là đóng góp rõ ràng nhất của vòng 2.5: thu hồi trọn vẹn một lớp trùng lặp mà vòng 2 mù hoàn toàn.')
p('5.2.2. Nhóm biến đổi hình học nhẹ và chất lượng', style='Heading 3')
p('Thu nhỏ 50% rồi phóng lại, nén JPEG chất lượng 40 và nhiễu Gaussian σ = 12 đều cho khoảng cách 0 ở cả ba dấu vân tay. Làm mờ Gaussian bán kính 2 cho edge_hash lệch 2 bit — vẫn an toàn trong ngưỡng — đồng thời kéo năng lượng cạnh xuống 0,58 lần, xác nhận edge_energy là tín hiệu phát hiện mờ khả thi (mục 5.3). Làm nét (unsharp mask) đẩy năng lượng cạnh lên 1,42 lần nhưng edge_hash chỉ lệch 4 bit: dấu vân tay cạnh ổn định trước cả hai chiều biến đổi độ nét.')
p('5.2.3. Nhóm biến đổi cấu trúc — giới hạn trung thực', style='Heading 3')
p('Crop là điểm yếu chung: crop 10% mỗi cạnh đã đẩy cả ba dấu vân tay ra ngoài ngưỡng (pHash 24, dHash 15, edge_hash 14); crop 25% còn tệ hơn (36, 35, 28). edge_hash có khá hơn nhưng không đủ để cứu — điều này đúng kỳ vọng, vì mọi hàm băm toàn cục đều thay đổi khi bố cục toàn ảnh thay đổi, và là lý do dự án vẫn cần vòng xác minh hình học (SIFT) trong lộ trình. Lật ngang phá cả ba dấu vân tay (32, 44, 32): không hàm băm nào trong ba hàm bất biến với phép lật. Một quan sát quan trọng khác: ảnh khác hoàn toàn cho khoảng cách 26 (pHash), 20 (dHash), 22 (edge_hash) — đều ngoài ngưỡng, tức khả năng phân biệt của edge_hash tương đương hai đàn anh; đồng thời khoảng cách của crop 25% (28) đã chồng lấn vùng của "ảnh khác" (22), cho thấy không thể nới ngưỡng để bắt crop mà không đánh đổi bằng báo giả. Kết luận thiết kế rút ra: giữ ngưỡng 10 và để Sobel làm lớp xác minh, không dùng làm tín hiệu nhóm độc lập.')
figure('fig_energy.png', 'Hình 5.2. Tỉ lệ năng lượng cạnh của một số biến thể so với ảnh gốc. Các cột đỏ là các biến thể làm giảm mạnh năng lượng cạnh (giảm sáng, tương phản thấp, làm mờ) — cơ sở cho cảnh báo ảnh kém chất lượng.', width_cm=13.5)
p('5.3. Đánh giá tín hiệu phát hiện ảnh mờ edge_energy', style='Heading 2')
p('Tỉ lệ năng lượng cạnh phản ứng đúng hướng với mọi biến đổi: giảm còn 0,58 khi làm mờ bán kính 2 và khoảng 0,47 khi làm mờ bán kính 3 (đo ở 128×128), tăng lên 1,42 khi làm nét, giảm còn 0,30 khi tương phản bị nén xuống 0,3. Cần nói rõ giới hạn: năng lượng cạnh cũng giảm khi ảnh bị giảm sáng (0,50) hay nén tương phản — tức tín hiệu này đo "độ giàu cấu trúc biểu kiến" chứ không tách riêng được nguyên nhân mờ. Vì vậy trong thiết kế, edge_energy chỉ được đề xuất làm cảnh báo mức warning trong bộ kiểm tra sức khỏe (giống các cảnh báo hiện có), không dùng làm căn cứ loại bỏ ảnh tự động.')
p('5.4. Thảo luận', style='Heading 2')
p('Ba kết luận lớn rút ra từ thực nghiệm. Thứ nhất, giá trị của Sobel trong dự án không nằm ở việc "thay thế" pHash/dHash — trên đa số biến đổi thông thường, ba dấu vân tay ngang nhau — mà nằm ở tính bổ sung: nó mã hóa một thuộc tính khác hẳn (cấu trúc cạnh thay vì tông màu/tần số), nên nó mạnh đúng ở điểm hai đàn anh yếu nhất. Thứ hai, cùng một đặc trưng cạnh cho ra hai sản phẩm: dấu vân tay để xác minh trùng lặp và năng lượng để cảnh báo chất lượng — hiệu quả đầu tư mã nguồn cao. Thứ ba, thực nghiệm cũng chứng minh điều Sobel không làm được (crop sâu, lật, xoay), qua đó giữ cho lộ trình vòng 4 của dự án nguyên vẹn giá trị. Nhóm cho rằng việc trình bày đầy đủ cả ba mặt này quan trọng hơn một bảng kết quả "toàn thắng", vì đó là cách đánh giá kỹ thuật trung thực.')
chapter_break()

# =====================================================================
# CHUONG 6 + TLTK + PHU LUC
# =====================================================================
p('Chương 6', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p('KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN', style='Heading 1')
p('6.1. Kết luận', style='Heading 2')
p('Báo cáo đã đi từ lý thuyết chung của học phần Xử lý ảnh — biến đổi điểm, lọc không gian, histogram, mặt phẳng bit — đến đào sâu bộ lọc Sobel: cơ sở gradient, cấu trúc kernel tách được gồm làm trơn nhân với đạo hàm, độ lớn và hướng cạnh, cùng vị trí của Sobel trong họ các toán tử phát hiện cạnh. Trên nền lý thuyết đó, nhóm đã tích hợp Sobel vào dự án thật VisionCleanse thành vòng xác minh 2.5 với ba hàm đặc trưng mới (sobel_magnitude, edge_hash, edge_energy), luật xác minh hai chiều trong tầng đối sánh, hai cờ dòng lệnh và 14 kiểm thử đơn vị; toàn bộ 88 kiểm thử của dự án đều đạt và hành vi mặc định không thay đổi.')
p('Thực nghiệm định lượng trên 17 trường hợp cho thấy: edge_hash bất biến hoàn toàn với phép âm bản (lệch 0 bit, nơi pHash lệch 62 và dHash lệch 64), ổn định trước thay đổi sáng, tương phản, gamma, làm mờ và làm nét; năng lượng cạnh là tín hiệu cảnh báo ảnh mờ khả thi (giảm còn khoảng 0,47 lần khi làm mờ Gaussian bán kính 3). Đồng thời nhóm cũng xác nhận các giới hạn: không hàm băm toàn cục nào — kể cả edge_hash — xử lý được crop sâu và lật ảnh.')
p('6.2. Hướng phát triển', style='Heading 2')
bullet('chia bản đồ cạnh Sobel thành lưới khối và băm từng khối để đối sánh từng phần, tiến tới bắt crop vừa trước khi cần tới SIFT.', bold_prefix='Đối sánh cạnh theo khối: ')
bullet('đưa cảnh báo năng lượng cạnh thấp vào bộ kiểm tra sức khỏe với ngưỡng hiệu chuẩn trên tập dữ liệu thật, kèm hình bản đồ cạnh trong báo cáo HTML để người dùng tự kiểm chứng.', bold_prefix='Hoàn thiện cảnh báo ảnh mờ: ')
bullet('đo precision/recall của vòng 2.5 trên một tập dữ liệu ảnh thật có gán nhãn trùng lặp, thay vì chỉ ảnh tổng hợp, và hiệu chuẩn ngưỡng Hamming theo dữ liệu.', bold_prefix='Đánh giá trên dữ liệu thật: ')
bullet('tiếp tục lộ trình vòng 4 (SIFT + RANSAC) cho crop sâu, xoay và lật — các biến đổi mà thực nghiệm đã chứng minh nằm ngoài tầm của mọi hàm băm toàn cục.', bold_prefix='Vòng xác minh hình học: ')
chapter_break()

p('TÀI LIỆU THAM KHẢO', style='Heading 1')
refs = [
    '[1] R. C. Gonzalez, R. E. Woods, Digital Image Processing, 4th edition, Pearson, 2018.',
    '[2] I. Sobel, G. Feldman, "A 3×3 Isotropic Gradient Operator for Image Processing", Stanford Artificial Intelligence Laboratory, 1968.',
    '[3] J. Canny, "A Computational Approach to Edge Detection", IEEE Transactions on Pattern Analysis and Machine Intelligence, 8(6), 1986, tr. 679–698.',
    '[4] C. Zauner, "Implementation and Benchmarking of Perceptual Image Hash Functions", luận văn thạc sĩ, University of Applied Sciences Upper Austria, 2010.',
    '[5] N. Dalal, B. Triggs, "Histograms of Oriented Gradients for Human Detection", CVPR 2005.',
    '[6] Dự án VisionCleanse — mã nguồn và tài liệu: https://github.com/MinhTriTM/vision-cleanse (nhánh vision-cleanse-BaiTapLonImageProcessing).',
    '[7] Tài liệu Pillow và NumPy: https://pillow.readthedocs.io; https://numpy.org/doc.',
]
for r in refs: p(r, space_after=4)
chapter_break()

p('PHỤ LỤC A. NỘI DUNG SLIDE THUYẾT TRÌNH', style='Heading 1')
p('Bộ slide gồm 16 slide, thời lượng trình bày dự kiến 12–15 phút. Mỗi mục dưới đây là một slide: tiêu đề, nội dung chính trên slide và gợi ý lời thoại.', italic=True)
slides = [
    ('Slide 1 — Trang bìa', 'Tiêu đề: "Bộ lọc Sobel trong phát hiện cạnh và tích hợp vào dự án VisionCleanse". Học phần Xử lý ảnh, lớp ĐHCNTT24A-CS – IN4152N01, GV: Trần Ngọc Thuận, danh sách 4 thành viên. Lời thoại: giới thiệu nhóm và chủ đề trong 20 giây.'),
    ('Slide 2 — Nội dung trình bày', '5 phần: (1) Cơ sở lý thuyết, (2) Bộ lọc Sobel chuyên sâu, (3) Dự án VisionCleanse, (4) Tích hợp vòng 2.5, (5) Thực nghiệm và kết luận.'),
    ('Slide 3 — Vì sao chọn Sobel?', 'Ba lý do: toán tử phát hiện cạnh kinh điển của học phần; là nền tảng của Canny và HOG; và nhóm có sẵn dự án thật (VisionCleanse) đang dùng gradient nguyên thủy dHash để đối chiếu và nâng cấp.'),
    ('Slide 4 — Bản đồ lý thuyết học phần', 'Sơ đồ các chủ đề: biến đổi điểm (âm bản, log, gamma, piecewise-linear), lọc không gian (trung bình, trung vị, Gaussian, Laplacian, Sobel, Prewitt), histogram, bit-plane — và vị trí của Sobel trong bản đồ đó.'),
    ('Slide 5 — Phát hiện cạnh và gradient', 'Định nghĩa cạnh; gradient là vector hai thành phần; độ lớn cho mức độ cạnh, hướng cho phương của cạnh. Hình minh họa một cạnh bậc thang và đáp ứng đạo hàm.'),
    ('Slide 6 — Hai kernel Sobel', 'Trình bày Gx, Gy; nhấn mạnh hệ số 2 ở giữa và cách phân tích kernel = vector làm trơn [1,2,1] nhân vector đạo hàm [−1,0,1]; so nhanh với Prewitt.'),
    ('Slide 7 — Ví dụ tính tay', 'Lân cận 3×3 có cạnh dọc (100 | 200): Gx = 400, Gy = 0, G = 400, hướng 0°. Kết luận: vùng phẳng cho đáp ứng 0, cạnh cho đáp ứng lớn.'),
    ('Slide 8 — Demo trực quan Sobel', 'Chèn Hình 2.1 của báo cáo: ảnh gốc → Gx → Gy → độ lớn gradient. Lời thoại: vùng phẳng tối đen, biên vật thể sáng lên; đây là "bản đồ cạnh".'),
    ('Slide 9 — So sánh các toán tử cạnh', 'Bảng 2.1 rút gọn: Roberts, Prewitt, Sobel, Laplacian theo bậc đạo hàm, độ nhạy nhiễu và ứng dụng. Kết luận: Sobel cân bằng nhất trong nhóm 3×3 bậc nhất.'),
    ('Slide 10 — Giới thiệu VisionCleanse', 'Bài toán làm sạch dataset và rò rỉ dữ liệu; kiến trúc các vòng 1 (MD5), 2 (pHash/dHash), 4 theo lộ trình (SIFT); khoảng trống giữa vòng 2 và 4.'),
    ('Slide 11 — dHash chính là gradient thô nhất', 'dHash = dấu của hiệu pixel kề phải = kernel [−1, +1], một chiều, không làm trơn. Sobel là phiên bản hoàn chỉnh hai chiều của cùng ý tưởng — cầu nối tự nhiên giữa lý thuyết và dự án.'),
    ('Slide 12 — Giới hạn hiện tại của dự án', 'README tự ghi: chưa bắt đổi màu mạnh; báo giả do bố cục giống; chưa phát hiện ảnh mờ. Phân tích gốc rễ: cả hai hàm băm đều mã hóa tông màu.'),
    ('Slide 13 — Thiết kế vòng 2.5', 'Sơ đồ: edge_hash (dấu vân tay cạnh 64 bit bằng ngưỡng trung vị), luật xác minh hai chiều cứu + phủ quyết, trường hợp edge_hash = 0 trả quyền cho luật cũ, cờ --sobel-verify.'),
    ('Slide 14 — Kết quả thực nghiệm nổi bật', 'Chèn Hình 5.1. Nhấn mạnh cột âm bản: pHash 62, dHash 64, edge_hash 0. Thông điệp: cạnh là cấu trúc, không phải tông màu.'),
    ('Slide 15 — Giới hạn trung thực và năng lượng cạnh', 'Crop 10% đã ngoài ngưỡng ở cả ba (24/15/14), lật ngang phá cả ba; edge_energy giảm còn 0,47 lần khi mờ r=3 → cảnh báo ảnh mờ. Nêu rõ điều Sobel không làm được.'),
    ('Slide 16 — Kết luận và hướng phát triển', 'Ba kết luận chính; bốn hướng phát triển (đối sánh theo khối, cảnh báo mờ, đánh giá dữ liệu thật, vòng SIFT). Kết thúc: cảm ơn thầy và lớp, mời đặt câu hỏi.'),
]
for title, body in slides:
    p(title, style='Heading 3')
    p(body)
chapter_break()

p('PHỤ LỤC B. HƯỚNG DẪN CHẠY DEMO', style='Heading 1')
p('B.1. Lấy mã nguồn', style='Heading 2')
code_block('git clone -b vision-cleanse-BaiTapLonImageProcessing https://github.com/MinhTriTM/vision-cleanse.git')
p('B.2. Chạy kiểm thử của vòng Sobel', style='Heading 2')
code_block('cd vision-cleanse\npip install -e .\npython -m pytest tests/test_sobel.py -q   # ky vong: 14 passed\npython -m pytest tests/ -q                # ky vong: 88 passed, 7 skipped')
p('B.3. Chạy công cụ với vòng 2.5 được bật', style='Heading 2')
code_block('visioncleanse ./dataset --sobel-verify --sobel-threshold 10')
p('B.4. Sinh hình bản đồ cạnh cho một ảnh bất kỳ (dùng cho slide)', style='Heading 2')
code_block('''python -c "from vision_cleanse.extractors import sobel_magnitude_image; sobel_magnitude_image('anh.jpg').save('ban_do_canh.png')"''')
p('— HẾT —', bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.save(str(BASE / 'BaoCao_Sobel_VisionCleanse.docx'))
print('saved docx')
