import pytest
from django.urls import reverse
from django.core.files import File
import tempfile

from django.contrib.auth.models import User
from customer.models import KhachHang
from cart.models import GioHang
from product.models import SanPham, MauSac, ChuyenMuc
from website.models import LoaiThongTin, ThongTin
from order.models import DonHang, ChiTietDonHang

@pytest.fixture
def setup_data():
    user = User.objects.create_user(username='testuser', password='12345')
    khachhang = KhachHang.objects.create(User=user)

    chuyenmuc = ChuyenMuc.objects.create(TenChuyenMuc='Chuyên mục A')
    mausac = MauSac.objects.create(TenMauSac='Red', MaMauSac='#FF0000')

    temp_image = tempfile.NamedTemporaryFile(suffix='.jpg')
    temp_image.write(b'Test image content')
    temp_image.seek(0)

    sanpham = SanPham.objects.create(
        TenSanPham='Sản phẩm A',
        MoTaNgan='Mô tả',
        GiaBan=50000,
        GiaKhuyenMai=70000,
        ChuyenMuc=chuyenmuc,
        AnhChinh=File(temp_image, name='test_image.jpg')
    )
    sanpham.MauSac.add(mausac)

    loai_phiship = LoaiThongTin.objects.create(MaLoai="phiship")
    loai_phivat = LoaiThongTin.objects.create(MaLoai="phivat")
    ThongTin.objects.create(LoaiThongTin=loai_phiship, GiaTri="30000")
    ThongTin.objects.create(LoaiThongTin=loai_phivat, GiaTri="5")

    return {
        'user': user,
        'khachhang': khachhang,
        'sanpham': sanpham,
        'mausac': mausac
    }

# ORDER001 
@pytest.mark.django_db
def test_ORDER001(client, setup_data):
    """ORDER001: Hiển thị giỏ hàng thành công khi có sản phẩm"""
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        GiaBan=50000,
        MauSac=setup_data['mausac']
    )

    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.context['title'] == 'Đặt hàng'
    assert response.context['giohang'].count() == 1
    assert response.context['khachhang'] == setup_data['khachhang']
    assert int(response.context['phiship']) == 30000
    assert int(response.context['phivat']) == 5
    assert response.context['thanhtoan'] == 135000
    assert response.templates[0].name == 'order/pay.html'

# ORDER002
@pytest.mark.django_db
def test_ORDER002(client, setup_data):
    """ORDER002: Đảm bảo hiển thị giỏ hàng thành công khi không có sản phẩm"""
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.context['title'] == 'Đặt hàng'
    assert response.context['giohang'].count() == 0
    assert response.context['khachhang'] == setup_data['khachhang']
    assert int(response.context['phiship']) == 30000
    assert int(response.context['phivat']) == 5
    assert response.context['thanhtoan'] == 0
    assert response.templates[0].name == 'order/pay.html'

# ORDER003
@pytest.mark.django_db
def test_ORDER003(client, setup_data):
    """ORDER003: Kiểm tra lỗi khi LoaiThongTin phiship không tồn tại"""
    LoaiThongTin.objects.filter(MaLoai="phiship").delete()
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Loại thông tin (phiship) không tồn tại!"}

# ORDER004
@pytest.mark.django_db
def test_ORDER004(client, setup_data):
    """ORDER004: Kiểm tra lỗi khi ThongTin phiship không tồn tại"""
    ThongTin.objects.filter(LoaiThongTin__MaLoai="phiship").delete()
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Thông tin (phiship) không tồn tại!"}

# ORDER005
@pytest.mark.django_db
def test_ORDER005(client, setup_data):
    """ORDER005: Kiểm tra lỗi khi LoaiThongTin phivat không tồn tại"""
    LoaiThongTin.objects.filter(MaLoai="phivat").delete()
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Loại thông tin (phivat) không tồn tại!"}

# ORDER006
@pytest.mark.django_db
def test_ORDER006(client, setup_data):
    """ORDER006: Kiểm tra lỗi khi ThongTin phivat không tồn tại"""
    ThongTin.objects.filter(LoaiThongTin__MaLoai="phivat").delete()
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Thông tin (phivat) không tồn tại!"}

# ORDER007
@pytest.mark.django_db
def test_ORDER007(client, setup_data):
    """ORDER007: Kiểm tra chuyển hướng khi giỏ hàng có sản phẩm thiếu màu sắc"""
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        GiaBan=50000,
        MauSac=None
    )
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.url == reverse('cart_list')

# ORDER008
@pytest.mark.django_db
def test_ORDER008(client, setup_data):
    """ORDER008: Kiểm tra chuyển hướng khi giỏ hàng có sản phẩm với số lượng bằng 0"""
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=0,
        GiaBan=50000,
        MauSac=setup_data['mausac']
    )
    client.force_login(setup_data['user'])
    response = client.get(reverse('pay_cart'), **{'HTTP_HOST': 'testserver'})

    assert response.url == reverse('cart_list')

# ORDER009
@pytest.mark.django_db
def test_ORDER009(client, setup_data):
    """ORDER009: Đảm bảo tạo đơn hàng thành công khi dữ liệu hợp lệ"""
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        GiaBan=50000,
        MauSac=setup_data['mausac']
    )

    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': 'Giao nhanh',
    },**{'HTTP_HOST': 'testserver'})

    donhang = DonHang.objects.get(KhachHang=setup_data['khachhang'])
    chitiet = ChiTietDonHang.objects.filter(DonHang=donhang)

    assert donhang.TongTien == 135000
    assert donhang.TrangThai == 'cxl'
    assert donhang.SoDienThoai == '0912345678'
    assert donhang.DiaChi == 'Hà Nội'
    assert donhang.GhiChu == 'Giao nhanh'
    assert chitiet.count() == 1
    assert response.url == reverse('home')

# ORDER010
@pytest.mark.django_db
def test_ORDER010(client, setup_data):
    """ORDER010: Kiểm tra lỗi khi số điện thoại không hợp lệ"""
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        GiaBan=50000,
        MauSac=setup_data['mausac']
    )

    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '12345',
        'diachi': 'Hà Nội',
        'ghichu': ''
    },**{'HTTP_HOST': 'testserver'})

    assert response.context['title'] == 'Đặt hàng'
    assert response.context['giohang'].count() == 1
    assert response.context['khachhang'] == setup_data['khachhang']
    assert int(response.context['phiship']) == 30000
    assert int(response.context['phivat']) == 5
    assert response.context['thanhtoan'] == 135000
    assert response.context['errorMessage'] == 'Vui Lòng Nhập Số Điện Thoại Hợp Lệ!'
    assert response.templates[0].name == 'order/pay.html'

# ORDER011
@pytest.mark.django_db
def test_ORDER011(client, setup_data):
    """ORDER011: Kiểm tra lỗi khi LoaiThongTin "phiship" không tồn tại"""
    LoaiThongTin.objects.filter(MaLoai="phiship").delete()
    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': ''
    }, **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Loại thông tin (phiship) không tồn tại!"}

# ORDER012
@pytest.mark.django_db
def test_ORDER012(client, setup_data):
    """ORDER012: Kiểm tra lỗi khi ThongTin "phiship" không tồn tại"""
    ThongTin.objects.filter(LoaiThongTin__MaLoai="phiship").delete()
    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': ''
    }, **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Thông tin (phiship) không tồn tại!"}

# ORDER013
@pytest.mark.django_db
def test_ORDER013(client, setup_data):
    """ORDER013: Kiểm tra lỗi khi LoaiThongTin "phivat" không tồn tại"""
    LoaiThongTin.objects.filter(MaLoai="phivat").delete()
    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': ''
    }, **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Loại thông tin (phivat) không tồn tại!"}

# ORDER014
@pytest.mark.django_db
def test_ORDER014(client, setup_data):
    """ORDER014: Kiểm tra lỗi khi ThongTin "phivat" không tồn tại"""
    ThongTin.objects.filter(LoaiThongTin__MaLoai="phivat").delete()
    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': ''
    }, **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Thông tin (phivat) không tồn tại!"}

# ORDER015
@pytest.mark.django_db
def test_ORDER015(client, setup_data):
    """ORDER015: Kiểm tra khi giỏ hàng rỗng nhưng dữ liệu hợp lệ"""
    client.force_login(setup_data['user'])
    response = client.post(reverse('pay_cart'), {
        'sodienthoai': '0912345678',
        'diachi': 'Hà Nội',
        'ghichu': ''
    }, **{'HTTP_HOST': 'testserver'})

    assert response.json() == {"error": "Không có sản phẩm nào trong giỏ để đặt hàng!"}
