from django.test import TestCase

# Create your tests here.
import pytest
from django.urls import reverse
from product.models import ChuyenMuc, SanPham
from website.models import Slide, BannerTop, BannerMid, BannerBottom
from news.models import TinTuc
from order.models import ChiTietDonHang, DonHang
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from customer.models import KhachHang
from order.models import DonHang

@pytest.fixture
def client():
    from django.test import Client
    return Client()

@pytest.fixture
def chuyen_muc():
    return ChuyenMuc.objects.create(TenChuyenMuc="Album KPOP")

@pytest.fixture
def slide(chuyen_muc):
    return Slide.objects.create(
        TieuDe="Slide 1",
        MoTaNgan="Ngắn",
        MoTaDai="Dài",
        ChuyenMuc=chuyen_muc,
        HienThi=True,
        HinhAnh=SimpleUploadedFile("slide.jpg", b"file_content", content_type="image/jpeg")
    )

from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def banner_top(chuyen_muc):
    return BannerTop.objects.create(
        HinhAnh=SimpleUploadedFile("banner_top.jpg", b"file_content", content_type="image/jpeg"),
        ChuyenMuc=chuyen_muc,
        HienThi=True
    )

@pytest.fixture
def banner_mid(chuyen_muc):
    return BannerMid.objects.create(
        HinhAnh=SimpleUploadedFile("banner_mid.jpg", b"file_content", content_type="image/jpeg"),
        ChuyenMuc=chuyen_muc,
        HienThi=True
    )

@pytest.fixture
def banner_bottom(chuyen_muc):
    return BannerBottom.objects.create(
        HinhAnh=SimpleUploadedFile("banner_bottom.jpg", b"file_content", content_type="image/jpeg"),
        ChuyenMuc=chuyen_muc,
        HienThi=True
    )

@pytest.fixture
def sanpham(chuyen_muc):
    return SanPham.objects.create(
        TenSanPham="Album BTS",
        GiaKhuyenMai=1000,
        GiaBan=900,
        MoTaNgan="Mô tả",
        MoTaDai="Chi tiết",
        ChuyenMuc=chuyen_muc,
        The="album",
        TrangThai=True,
        AnhChinh=SimpleUploadedFile("sanpham.jpg", b"file_content", content_type="image/jpeg")  # ✅ Thêm dòng này

    )

@pytest.fixture
def tintuc():
    return TinTuc.objects.create(
        TieuDe="Tin KPOP HOT",
        AnhChinh=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
        The="kpop",
        NoiDung="Nội dung",
    )

@pytest.fixture
def top_product(sanpham):
    # Tạo user
    user = User.objects.create_user(username="testuser", password="testpass", first_name="Test", last_name="User")

# Tạo khách hàng liên kết với user đó
    khach_hang = KhachHang.objects.create(User=user)
    don_hang = DonHang.objects.create(
    KhachHang=khach_hang,
    SoDienThoai="0123456789",
    DiaChi="Hà Nội",
    TongTien=100000,
    TrangThai="cxl")
    return ChiTietDonHang.objects.create(DonHang=don_hang, SanPham=sanpham, SoLuong=2)

# ✅ TEST CASE
@pytest.mark.django_db
def test_home_view(client, slide, banner_top, banner_mid, banner_bottom, sanpham, tintuc, top_product):
    """
    STT: 1
    Chức năng: Truy cập trang chủ
    Phương thức: GET
    Mã Testcase: TC_HOME_01
    Mục tiêu: Kiểm tra dữ liệu trả về từ Home view có đủ tất cả thành phần không
    Input: GET request tới URL '/'
    Expected Output: HTTP 200, template 'website/home.html', context đầy đủ: sản phẩm, slide, banner, tin tức, top sản phẩm
    Ghi chú: Đảm bảo thứ tự dữ liệu đúng theo limit, ordering
    """
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert response.templates[0].name == 'website/home.html'

    ctx = response.context

    assert "sanpham" in ctx and ctx["sanpham"].count() == 1
    assert "slide" in ctx and ctx["slide"].count() == 1
    assert "bannertop" in ctx and ctx["bannertop"].count() == 1
    assert "bannermid" in ctx and ctx["bannermid"].count() == 1
    assert "bannerbottom" in ctx and ctx["bannerbottom"].count() == 1
    assert "tintuc" in ctx and ctx["tintuc"].count() == 1
    assert "top_products" in ctx and len(ctx["top_products"]) == 1
    assert ctx["title"] == "Cửa Hàng KPOP Chất Lượng, Giá Rẻ!"

@pytest.mark.django_db
def test_home_view_empty_data(client):
    """
    STT: 2
    Mã Testcase: TC_HOME_02
    Mục tiêu: Kiểm tra khi không có dữ liệu nào, view vẫn trả về HTTP 200 và context rỗng đúng định dạng
    """
    response = client.get(reverse("home"))
    assert response.status_code == 200
    ctx = response.context

    assert "sanpham" in ctx and ctx["sanpham"].count() == 0
    assert "slide" in ctx and ctx["slide"].count() == 0
    assert "bannertop" in ctx and ctx["bannertop"].count() == 0
    assert "bannermid" in ctx and ctx["bannermid"].count() == 0
    assert "bannerbottom" in ctx and ctx["bannerbottom"].count() == 0
    assert "tintuc" in ctx and ctx["tintuc"].count() == 0
    assert "top_products" in ctx and len(ctx["top_products"]) == 0

@pytest.mark.django_db
def test_home_view_limit_sanpham_tintuc(client, chuyen_muc):
    """
    STT: 3
    Mã Testcase: TC_HOME_03
    Mục tiêu: Kiểm tra giới hạn số lượng sản phẩm và tin tức
    """
    # Tạo 15 sản phẩm, chỉ 12 cái đầu mới lấy
    for i in range(15):
        SanPham.objects.create(
            TenSanPham=f"SP{i}",
            GiaKhuyenMai=1000,
            GiaBan=900,
            MoTaNgan="Mô tả",
            MoTaDai="Chi tiết",
            ChuyenMuc=chuyen_muc,
            The="album",
            TrangThai=True,
            AnhChinh=SimpleUploadedFile(f"sp{i}.jpg", b"abc", content_type="image/jpeg")
        )

    # Tạo 20 tin tức, lấy 10 cái đầu
    for i in range(20):
        TinTuc.objects.create(
            TieuDe=f"News {i}",
            AnhChinh=SimpleUploadedFile(f"news{i}.jpg", b"abc", content_type="image/jpeg"),
            The="kpop",
            NoiDung="Nội dung"
        )

    response = client.get(reverse("home"))
    ctx = response.context

    assert ctx["sanpham"].count() == 12
    assert ctx["tintuc"].count() == 10
