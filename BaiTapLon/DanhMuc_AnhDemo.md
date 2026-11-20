# Danh mục ảnh demo — 44 ảnh cho báo cáo và slide

Sinh tự động bằng `scripts/make_demo_images.py` (numpy/Pillow/scipy + chính code Sobel của dự án). Ảnh nền là một **cảnh tổng hợp** (nhà, núi, mặt trời, cây, bàn cờ, sọc chéo) có cạnh ở nhiều hướng.

⚠️ **Lưu ý số liệu:** các khoảng cách Hamming in trên ảnh của thư mục `06_bien_the/` được tính trực tiếp trên ảnh cảnh tổng hợp này (âm bản vẫn cho pHash 62, dHash 59, edge 0 — cùng hiện tượng). **Số liệu chính thức trong Chương 5 của báo cáo vẫn là `experiment/results.json`** (đo trên fixture `photo_like`: âm bản 62/64/0). Đừng trộn hai bộ số trong cùng một bảng.

## 01_sobel_co_ban/ — Chương 2 (Sobel), slide 6–9
| File | Nội dung | Gợi ý chú thích |
|---|---|---|
| sobel_01_anh_goc_xam.png | Ảnh cảnh gốc dạng xám | Ảnh kiểm tra tổng hợp dùng cho các demo Sobel |
| sobel_02_Gx.png | Thành phần Gx (có dấu, 0 = xám giữa) | Gx làm nổi bật cạnh dọc |
| sobel_03_Gy.png | Thành phần Gy | Gy làm nổi bật cạnh ngang |
| sobel_04_do_lon_gradient.png | Độ lớn G = √(Gx²+Gy²) | Bản đồ độ lớn gradient |
| sobel_05_huong_gradient.png | Hướng gradient mã hóa theo mức xám | Hướng cạnh θ = atan2(Gy, Gx) |
| sobel_06_ban_do_canh_nguong.png | Nhị phân hóa độ lớn theo ngưỡng | Bản đồ cạnh sau ngưỡng hóa |
| sobel_07_ghep_4_hinh.png | Ghép 4: gốc / Gx / Gy / G | Hình tổng hợp kinh điển cho slide Sobel |
| sobel_08a_canh_bac_100_200.png | Cạnh bậc 100→200 | Ảnh đầu vào của ví dụ tính tay |
| sobel_08b_do_thi_Gx.png | Đồ thị Gx qua cạnh bậc, đỉnh 400 | Gx đạt 400 đúng tại biên — khớp ví dụ tính tay |
| sobel_08c_Gx_canh_bac.png | Ảnh Gx của cạnh bậc | Đáp ứng Gx chỉ xuất hiện tại cột biên |
| sobel_09_L2_vs_L1.png | So sánh G (L2) và \|Gx\|+\|Gy\| (L1) | Hai cách tính độ lớn gradient |
| sobel_10_nhay_nhieu.png | Nhiễu σ=18: Sobel trực tiếp vs mờ-trước | Đạo hàm khuếch đại nhiễu; làm mờ Gaussian trước giúp ổn định |

## 02_so_sanh_toan_tu/ — Chương 2 (so sánh), slide 9
| File | Nội dung |
|---|---|
| cmp_01_roberts.png / cmp_02_prewitt.png / cmp_03_sobel.png / cmp_04_scharr.png | Độ lớn gradient theo từng toán tử |
| cmp_05_laplacian.png | Laplacian (đạo hàm bậc hai, có dấu) |
| cmp_06_ghep_so_sanh.png | Ghép 6 hình: 5 toán tử + ảnh gốc — hình so sánh chính cho báo cáo |

## 03_14_chu_de/ — Chương 1 (14 chủ đề), slide 3–5
| File | Chủ đề |
|---|---|
| t00_anh_mau_goc.png | Ảnh màu gốc (bản có màu của ảnh cảnh) |
| t01_loc_trung_binh.png | 4. Lọc trung bình |
| t01_trung_binh_vs_t02_trung_vi.png | So sánh trung bình vs trung vị trên nhiễu muối tiêu |
| t02_loc_trung_vi.png | 5. Lọc trung vị |
| t03_loc_gaussian.png | 6. Lọc Gaussian |
| t04_laplacian_tang_net.png | 7. Lạp Laplacian + tăng nét (gốc / Laplacian / ảnh tăng nét) |
| t05_loc_sobel.png | 8. Lọc Sobel |
| t06_loc_prewitt.png | 9. Lọc Prewitt |
| t07_thresholding_otsu.png | 10. Xử lý theo ngưỡng: cố định 128 vs Otsu tự động |
| t08_loc_khong_gian_dap_ung_xung.png | 11. Lọc không gian qua đáp ứng xung |
| t09_bien_doi_am_ban.png | 1. Biến đổi âm bản (trên ảnh màu) |
| t10_bien_doi_logarit.png | 2. Biến đổi Logarit |
| t11_bien_doi_gamma.png | 3. Power-Law/Gamma với γ = 0.45 / 1 / 1.8 / 2.6 |
| t12_piecewise_linear.png | 12. Piecewise-Linear: kéo dãn tương phản |
| t13_cat_bit_plane.png | 13. Cắt Bit-plane: đủ 8 mặt phẳng bit 7→0 |
| t14_can_bang_histogram.png | 14. Cân bằng Histogram: ảnh + histogram trước/sau |

## 04_pipeline_hash/ — Chương 3 (VisionCleanse), slide 10–11
| File | Nội dung | Gợi ý chú thích |
|---|---|---|
| hash_01_cac_buoc_phash.png | 4 bước pHash: 32×32 → DCT → khối tần thấp 8×8 → lưới bit | Quy trình pHash (Zauner 2010) |
| hash_02_cac_buoc_dhash.png | 9×8 → lưới bit dHash | dHash ghi dấu hiệu pixel kề — gradient [−1,+1] |
| hash_03_hamming_am_ban.png | pHash gốc vs âm bản, bản đồ bit lệch | 62/64 bit lệch — pHash "mù" trước âm bản |

## 05_edge_hash/ — Chương 4 (tích hợp), slide 12–13
| File | Nội dung | Gợi ý chú thích |
|---|---|---|
| edge_01_cac_buoc_edge_hash.png | Độ lớn Sobel 32×32 → trung bình khối 8×8 → lưới bit | Quy trình edge_hash của vòng 2.5 |
| edge_02_bat_bien_am_ban.png | Độ lớn Sobel và edge hash của gốc vs âm bản | Hai bản đồ độ lớn giống hệt nhau; hai hash lệch 0 bit |
| edge_03_nang_luong_canh_va_mo.png | Chuỗi mờ Gaussian r=0..3 + năng lượng cạnh | Năng lượng cạnh sụt theo độ mờ — cơ sở phát hiện ảnh mờ |

## 06_bien_the/ — Chương 5 (thực nghiệm), slide 14
| File | Nội dung |
|---|---|
| var_00_ghep_bien_the.png | Ghép 13 biến thể, mỗi biến thể ghi 3 khoảng cách Hamming đo trực tiếp trên ảnh cảnh |
| var_01_am_ban.png / var_02_crop25.png / var_03_lat_ngang.png | Ba biến thể tiêu biểu đặt cạnh ảnh gốc |
