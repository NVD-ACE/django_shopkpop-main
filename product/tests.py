# product/tests.py
from django.test import TestCase
from .models import SanPham, ChuyenMuc, MauSac
from django.utils.text import slugify

class SanPhamModelTest(TestCase):
    def setUp(self):
        self.chuyenmuc = ChuyenMuc.objects.create(
            TenChuyenMuc="Áo Kpop",
            DuongDan=slugify("Áo Kpop")
        )
        self.mausac = MauSac.objects.create(
            TenMauSac="Đen",
            MaMauSac="#000000"
        )
    def test_sanpham_save(self):
        sanpham = SanPham(
            TenSanPham="Áo thun BTS",
            GiaBan=200000,
            GiaKhuyenMai=150000,
            MoTaNgan="Áo thun đẹp",
            MoTaDai="<p>Áo thun chất lượng cao</p>",
            ChuyenMuc=self.chuyenmuc,
            TrangThai=True
        )
        sanpham.save()
        sanpham.MauSac.add(self.mausac)
        saved_sanpham = SanPham.objects.get(TenSanPham="Áo thun BTS")
        
        self.assertEqual(saved_sanpham.TenSanPham, "Áo thun BTS")
        self.assertEqual(saved_sanpham.GiaBan, 200000)
        self.assertEqual(saved_sanpham.GiaKhuyenMai, 150000)
        self.assertEqual(saved_sanpham.DuongDan, slugify("Áo thun BTS"))
        self.assertAlmostEqual(saved_sanpham.PhanTramGiam, -33.33, places=2) 
        self.assertEqual(saved_sanpham.ChuyenMuc, self.chuyenmuc)
        self.assertTrue(saved_sanpham.TrangThai)
        self.assertEqual(saved_sanpham.MauSac.count(), 1)
        
        # Kiểm tra sửa
        saved_sanpham.GiaBan = 250000
        saved_sanpham.save()
        self.assertEqual(SanPham.objects.get(TenSanPham="Áo thun BTS").GiaBan, 250000)
        
        # Kiểm tra xóa
        sanpham_count_before = SanPham.objects.count()
        saved_sanpham.delete()
        self.assertEqual(SanPham.objects.count(), sanpham_count_before - 1)
# product/tests.py
# import pytest
# from .models import SanPham, ChuyenMuc, MauSac
# from django.utils.text import slugify
 
# # Đánh dấu đây là test dùng Django database
# @pytest.mark.django_db
# def test_sanpham_save():
#     # Tạo dữ liệu mẫu (tương đương setUp)
#     chuyenmuc = ChuyenMuc.objects.create(
#         TenChuyenMuc="Áo Kpop",
#         DuongDan=slugify("Áo Kpop")
#     )
#     mausac = MauSac.objects.create(
#         TenMauSac="Đen",
#         MaMauSac="#000000"
#     )
    
#     # Tạo sản phẩm
#     sanpham = SanPham(
#         TenSanPham="Áo thun BTS",
#         GiaBan=200000,
#         GiaKhuyenMai=150000,
#         MoTaNgan="Áo thun đẹp",
#         MoTaDai="<p>Áo thun chất lượng cao</p>",
#         ChuyenMuc=chuyenmuc,
#         TrangThai=True
#     )
#     sanpham.save()
#     sanpham.MauSac.add(mausac)

#     # Lấy sản phẩm từ DB
#     saved_sanpham = SanPham.objects.get(TenSanPham="Áo thun BTS")

#     # Kiểm tra các giá trị
#     assert saved_sanpham.TenSanPham == "Áo thun BTS"
#     assert saved_sanpham.GiaBan == 200000
#     assert saved_sanpham.GiaKhuyenMai == 150000
#     assert saved_sanpham.DuongDan == slugify("Áo thun BTS")
#     assert saved_sanpham.PhanTramGiam == pytest.approx(-33.33, abs=0.01)  # Kiểm tra gần đúng
#     assert saved_sanpham.ChuyenMuc == chuyenmuc
#     assert saved_sanpham.TrangThai is True
#     assert saved_sanpham.MauSac.count() == 1

#     # Kiểm tra sửa
#     saved_sanpham.GiaBan = 250000
#     saved_sanpham.save()
#     assert SanPham.objects.get(TenSanPham="Áo thun BTS").GiaBan == 250000

#     # Kiểm tra xóa
#     sanpham_count_before = SanPham.objects.count()
#     saved_sanpham.delete()
#     assert SanPham.objects.count() == sanpham_count_before - 1
# # Test mới cho ChuyenMuc
# @pytest.mark.django_db
# def test_chuyenmuc_save():
#     # Tạo chuyên mục
#     chuyenmuc = ChuyenMuc(
#         TenChuyenMuc="Quần Kpop",
#         DuongDan=slugify("Quần Kpop")  # Sẽ được tự động tạo bởi save()
#     )
#     chuyenmuc.save()

#     # Lấy chuyên mục từ DB
#     saved_chuyenmuc = ChuyenMuc.objects.get(TenChuyenMuc="Quần Kpop")

#     # Kiểm tra các giá trị
#     assert saved_chuyenmuc.TenChuyenMuc == "Quần Kpop"
#     assert saved_chuyenmuc.DuongDan == slugify("Quần Kpop")
#     assert saved_chuyenmuc.created_at is not None
#     assert saved_chuyenmuc.updated_at is not None

#     # Kiểm tra sửa
#     saved_chuyenmuc.TenChuyenMuc = "Quần Kpop Mới"
#     saved_chuyenmuc.save()
#     updated_chuyenmuc = ChuyenMuc.objects.get(id=saved_chuyenmuc.id)
#     assert updated_chuyenmuc.TenChuyenMuc == "Quần Kpop Mới"
#     assert updated_chuyenmuc.DuongDan == slugify("Quần Kpop Mới")  # Đường dẫn cũng được cập nhật

#     # Kiểm tra xóa
#     chuyenmuc_count_before = ChuyenMuc.objects.count()
#     saved_chuyenmuc.delete()
#     assert ChuyenMuc.objects.count() == chuyenmuc_count_before - 1