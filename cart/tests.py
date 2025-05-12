import pytest
import tempfile
from django.urls import reverse

from django.core.files import File
from django.contrib.auth.models import User
from customer.models import KhachHang
from cart.models import GioHang
from product.models import SanPham, MauSac, ChuyenMuc
from website.models import LoaiThongTin, ThongTin

@pytest.fixture
def setup_data():
    """Fixture để thiết lập dữ liệu chung cho các test. - Fixture chạy trước mỗi test."""
    user = User.objects.create(id=1, username='testuser')
    khachhang = KhachHang.objects.create(User=user)
    chuyenmuc = ChuyenMuc.objects.create(id=1, TenChuyenMuc='Test Category')
    mausac = MauSac.objects.create(id=1, TenMauSac='Red', MaMauSac='#FF0000')
    loai_phiship = LoaiThongTin.objects.create(MaLoai="phiship")
    loai_phivat = LoaiThongTin.objects.create(MaLoai="phivat")
    phiship = ThongTin.objects.create(LoaiThongTin=loai_phiship, GiaTri="30000")
    phivat = ThongTin.objects.create(LoaiThongTin=loai_phivat, GiaTri="5")
    
    # Tạo file ảnh tạm thời
    temp_image = tempfile.NamedTemporaryFile(suffix='.jpg')
    temp_image.write(b'Test image content') 
    temp_image.seek(0)
    
    sanpham = SanPham.objects.create(
        id=1,
        TenSanPham='Test Product',
        MoTaNgan='Short Desc',
        GiaBan=50000,
        GiaKhuyenMai=70000,
        ChuyenMuc=chuyenmuc,
        AnhChinh=File(temp_image, name='test_image.jpg')
    )
    sanpham.MauSac.add(mausac)  

    return {
        'user': user,
        'khachhang': khachhang,
        'sanpham': sanpham,
        'mausac': mausac,
        'phiship': phiship,
        'phivat': phivat
    }

#CART001
@pytest.mark.django_db
def test_CART001(client, setup_data):
    """CART001: Đảm bảo hiển thị giỏ hàng thành công khi có sản phẩm."""
    # Tạo dữ liệu giỏ hàng
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        MauSac=setup_data['mausac']
    )
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET đến URL giỏ hàng
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})

    # Kiểm tra template và context
    assert response.templates[0].name == 'cart/list.html'
    assert response.context['title'] == "Giỏ hàng"
    assert response.context['giohang'].count() == 1
    assert response.context['mausac'].count() == 1
    assert response.context['thanhtoan'] == 135000
    assert response.context['phiship'] == "30000"
    assert response.context['phivat'] == "5"
    assert response.context['total_price'] == 100000
    assert response.context['giohang'][0].SoLuong == 2

#CART002
@pytest.mark.django_db
def test_CART002(client, setup_data):
    """CART002: Đảm bảo hiển thị giỏ hàng thành công khi không có sản phẩm."""

    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET đến URL giỏ hàng (Giỏ hàng rỗng)
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})

    # Kiểm tra template và context
    assert response.templates[0].name == 'cart/list.html'
    assert response.context['title'] == "Giỏ hàng"
    assert response.context['giohang'].count() == 0  
    assert response.context['mausac'].count() > 0  
    assert response.context['thanhtoan'] == 0  
    assert response.context['phiship'] == "30000"
    assert response.context['phivat'] == "5"  
    assert response.context['total_price'] == 0  

# CART003 
@pytest.mark.django_db
def test_CART003(client, setup_data):
    """CART003: Kiểm tra lỗi khi LoaiThongTin phiship không tồn tại."""

    # Đăng nhập người dùng hợp lệ
    client.force_login(setup_data['user'])

    # Xóa LoaiThongTin có mã "phiship"
    LoaiThongTin.objects.all().filter(MaLoai="phiship").delete()

    # Thực hiện yêu cầu GET đến URL giỏ hàng
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})

    # Kiểm tra lỗi trả về
    assert response.json() == {"error": "Loại thông tin (phiship) không tồn tại!"}
    
# CART004 
@pytest.mark.django_db
def test_CART004(client, setup_data):
    """CART004: Kiểm tra lỗi khi ThongTin phiship không tồn tại."""

    # Đăng nhập người dùng hợp lệ
    client.force_login(setup_data['user'])

    # Xóa ThongTin có LoaiThongTin "phiship"
    ThongTin.objects.all().filter(LoaiThongTin__MaLoai="phiship").delete()

    # Thực hiện yêu cầu GET đến URL giỏ hàng
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})
    
    # Kiểm tra lỗi trả về
    assert response.json() == {"error": "Thông tin (phiship) không tồn tại!"}

# CART005 
@pytest.mark.django_db
def test_CART005(client, setup_data):
    """CART005: Kiểm tra lỗi khi LoaiThongTin phivat không tồn tại."""

    # Đăng nhập người dùng hợp lệ
    client.force_login(setup_data['user'])

    # Xóa LoaiThongTin có mã "phivat"
    LoaiThongTin.objects.all().filter(MaLoai="phivat").delete()

    # Thực hiện yêu cầu GET đến URL giỏ hàng
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})
    
    # Kiểm tra lỗi trả về
    assert response.json() == {"error": "Loại thông tin (phivat) không tồn tại!"}

# CART006 
@pytest.mark.django_db
def test_CART006(client, setup_data):
    """CART006: Kiểm tra lỗi khi ThongTin phivat không tồn tại."""

    # Đăng nhập người dùng hợp lệ
    client.force_login(setup_data['user'])

    # Xóa ThongTin có LoaiThongTin "phivat"
    ThongTin.objects.all().filter(LoaiThongTin__MaLoai="phivat").delete()

    # Thực hiện yêu cầu GET đến URL giỏ hàng
    response = client.get(reverse('cart_list'), **{'HTTP_HOST': 'testserver'})
    
    # Kiểm tra lỗi trả về
    assert response.json() == {"error": "Thông tin (phivat) không tồn tại!"}

# CART007
@pytest.mark.django_db
def test_CART007(client, setup_data):
    """CART007: Kiểm tra trả về lỗi khi user chưa đăng nhập"""
    
    # Thực hiện yêu cầu POST đến URL thêm sản phẩm vào giỏ hàng
    response = client.post(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id,
        'mausac': setup_data['mausac'].id,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "Vui Lòng Đăng Nhập Để Thêm Sản Phẩm Vào Giỏ Hàng!"}

# CART008
@pytest.mark.django_db
def test_CART008(client, setup_data):
    """CART008: Đảm bảo thêm sản phẩm thành công qua POST"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu POST đến URL thêm sản phẩm vào giỏ hàng
    response = client.post(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id,
        'mausac': setup_data['mausac'].id,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"success": "Thêm Sản Phẩm Vào Giỏ Hàng Thành Công!"}

    # Kiểm tra sản phẩm đã được thêm vào giỏ hàng
    giohang = GioHang.objects.filter(KhachHang=setup_data['khachhang'], SanPham=setup_data['sanpham'])
    assert giohang.count() == 1
    assert giohang.first().SoLuong == 1

# CART009
@pytest.mark.django_db
def test_CART009(client, setup_data):
    """CART009: Kiểm tra lỗi khi thiếu masanpham trong POST"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu POST thiếu 'masanpham'
    response = client.post(reverse('add_product_cart'), {
        'mausac': setup_data['mausac'].id,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "masanpham không được để trống!"}

# CART010 - bỏ vì không thể sảy ra trường hợp này
# @pytest.mark.django_db
# def test_CART010(client, setup_data):
#     """CART010: Kiểm tra lỗi khi mamausac bằng 0 trong POST"""
    
#     # Đăng nhập người dùng
#     client.force_login(setup_data['user'])

#     # Thực hiện yêu cầu POST với mamausac = 0
#     response = client.post(reverse('add_product_cart'), {
#         'masanpham': setup_data['sanpham'].id,
#         'mausac': "",
#         'soluong': 1
#     }, **{'HTTP_HOST': 'testserver'})

#     # Kiểm tra mã trạng thái HTTP
#     assert response.json() == {"error": "Vui Lòng Chọn Màu Sắc!"}

# CART011
@pytest.mark.django_db
def test_CART011(client, setup_data):
    """CART011: Kiểm tra lỗi khi soluong nhỏ hơn hoặc bằng 0 trong POST"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu POST với soluong = 0
    response = client.post(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id,
        'mausac': setup_data['mausac'].id,
        'soluong': 0
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "Số Lượng Sản Phẩm Phải Lớn Hơn 0!"}

# CART012
@pytest.mark.django_db
def test_CART012(client, setup_data):
    """CART012: Kiểm tra lỗi khi masanpham không phải số trong POST"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu POST với masanpham không phải là số
    response = client.post(reverse('add_product_cart'), {
        'masanpham': 'abc',
        'mausac': setup_data['mausac'].id,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "masanpham phải là số nguyên!"}

# CART013
@pytest.mark.django_db
def test_CART013(client, setup_data):
    """CART013: Kiểm tra lỗi khi sản phẩm đã có trong giỏ qua POST"""
    
    # Tạo giỏ hàng với sản phẩm đã có
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )

    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu POST với sản phẩm đã có trong giỏ
    response = client.post(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id,
        'mausac': setup_data['mausac'].id,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "Sản Phẩm Đã Có Trong Giỏ Hàng!"}

# CART014
@pytest.mark.django_db
def test_CART014(client, setup_data):
    """CART014: Đảm bảo thêm sản phẩm thành công qua GET"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET để thêm sản phẩm vào giỏ hàng
    response = client.get(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"success": "Thêm Sản Phẩm Vào Giỏ Hàng Thành Công!"}

    # Kiểm tra sản phẩm đã được thêm vào giỏ hàng
    giohang = GioHang.objects.filter(KhachHang=setup_data['khachhang'], SanPham=setup_data['sanpham'])
    assert giohang.count() == 1

# CART015
@pytest.mark.django_db
def test_CART015(client, setup_data):
    """CART015: Kiểm tra lỗi khi thiếu masanpham trong GET"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET thiếu 'masanpham'
    response = client.get(reverse('add_product_cart'), {}, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "masanpham không được để trống!"}

# CART016
@pytest.mark.django_db
def test_CART016(client, setup_data):
    """CART016: Kiểm tra lỗi khi masanpham không phải số trong GET"""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET với masanpham không phải là số
    response = client.get(reverse('add_product_cart'), {
        'masanpham': 'abc'
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "masanpham phải là số nguyên!"}

# CART017
@pytest.mark.django_db
def test_CART017(client, setup_data):
    """CART017: Kiểm tra lỗi khi sản phẩm đã có trong giỏ qua GET"""
    
    # Tạo giỏ hàng với sản phẩm đã có
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )

    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện yêu cầu GET với sản phẩm đã có trong giỏ
    response = client.get(reverse('add_product_cart'), {
        'masanpham': setup_data['sanpham'].id
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra mã trạng thái HTTP
    assert response.json() == {"error": "Sản Phẩm Đã Có Trong Giỏ Hàng!"}

# CART018
@pytest.mark.django_db
def test_CART018(client, setup_data):
    """CART018: Kiểm tra trả về lỗi khi user chưa đăng nhập."""
    
    # Thực hiện POST request mà không cần đăng nhập
    response = client.post(reverse('update_number_cart'), {
        'magiohang': 1,
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra phản hồi có chứa lỗi yêu cầu đăng nhập
    assert response.json() == {"error": "Vui Lòng Đăng Nhập!"}

# CART019
@pytest.mark.django_db
def test_CART019(client, setup_data):
    """CART019: Đảm bảo cập nhật số lượng thành công."""
    # Tạo dữ liệu giỏ hàng
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện POST request để cập nhật số lượng sản phẩm trong giỏ hàng
    response = client.post(reverse('update_number_cart'), {
        'magiohang': giohang.id,
        'soluong': 2
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra phản hồi thành công
    assert response.json() == {"success": "Cập Nhật Số Lượng Sản Phẩm Thành Công!"}

# CART020
@pytest.mark.django_db
def test_CART020(client, setup_data):
    """CART020: Kiểm tra lỗi khi thiếu magiohang."""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện POST request thiếu 'magiohang'
    response = client.post(reverse('update_number_cart'), {
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra lỗi phản hồi
    assert response.json() == {"error": "magiohang không được để trống!"}

# CART021
@pytest.mark.django_db
def test_CART021(client, setup_data):
    """CART021: Kiểm tra lỗi khi thiếu soluong."""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện POST request thiếu 'soluong'
    response = client.post(reverse('update_number_cart'), {
        'magiohang': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra lỗi phản hồi
    assert response.json() == {"error": "soluong không được để trống!"}

# CART022
@pytest.mark.django_db
def test_CART022(client, setup_data):
    """CART022: Kiểm tra lỗi khi soluong nhỏ hơn hoặc bằng 0."""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện POST request với 'soluong' = 0
    response = client.post(reverse('update_number_cart'), {
        'magiohang': 1,
        'soluong': 0
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra lỗi phản hồi
    assert response.json() == {"error": "Số Lượng Phải Lớn Hơn 0!"}

# # CART023 - bỏ vì không thể sảy ra trường hợp này
# @pytest.mark.django_db
# def test_CART023(client, setup_data):
#     """CART023: Kiểm tra lỗi khi soluong là chuỗi trống."""
    
#     # Đăng nhập người dùng
#     client.force_login(setup_data['user'])

#     # Thực hiện POST request với 'soluong' là chuỗi trống
#     response = client.post(reverse('update_number_cart'), {
#         'magiohang': 1,
#         'soluong': ""
#     }, **{'HTTP_HOST': 'testserver'})

#     # Kiểm tra lỗi phản hồi
#     assert response.json() == {"error": "Không Được Bỏ Trống Số Lượng!"}

# CART024
@pytest.mark.django_db
def test_CART024(client, setup_data):
    """CART024: Kiểm tra lỗi khi magiohang không tồn tại."""
    
    # Đăng nhập người dùng
    client.force_login(setup_data['user'])

    # Thực hiện POST request với 'magiohang' không tồn tại
    response = client.post(reverse('update_number_cart'), {
        'magiohang': 999,  # ID giỏ hàng không tồn tại
        'soluong': 1
    }, **{'HTTP_HOST': 'testserver'})

    # Kiểm tra lỗi phản hồi
    assert response.json() == {"error": "Giỏ hàng không tồn tại!"}

# CART025
@pytest.mark.django_db
def test_CART025(client, setup_data):
    """CART025: Kiểm tra trả về lỗi khi user chưa đăng nhập."""
    response = client.post(reverse('update_color_cart'), {
        'magiohang': 1,
        'mamau': 1
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Vui Lòng Đăng Nhập!"}

# CART026
@pytest.mark.django_db
def test_CART026(client, setup_data):
    """CART026: Đảm bảo cập nhật màu thành công."""
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    mausac_update = MauSac.objects.create(id=2, TenMauSac='Blue', MaMauSac='#0000FF')
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'magiohang': giohang.id,
        'mamau': mausac_update.id
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"success": "Cập Nhật Màu Sản Phẩm Thành Công!"}

# CART027
@pytest.mark.django_db
def test_CART027(client, setup_data):
    """CART027: Kiểm tra lỗi khi thiếu magiohang."""
    mausac_update = MauSac.objects.create(id=2, TenMauSac='Blue', MaMauSac='#0000FF')
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'mamau': mausac_update.id
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "magiohang không được để trống!"}

# CART028
@pytest.mark.django_db
def test_CART028(client, setup_data):
    """CART028: Kiểm tra lỗi khi thiếu mamau"""
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'magiohang': giohang.id
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "mamau không được để trống!"}

# CART029
@pytest.mark.django_db
def test_CART029(client, setup_data):
    """CART029: Kiểm tra lỗi khi 'mamau' nhỏ hơn hoặc bằng 0."""
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'magiohang': giohang.id,
        'mamau': 0
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Vui Lòng Chọn Lại Màu Hợp Lệ!"}

# CART030 - bỏ vì không thể sảy ra trường hợp này
# @pytest.mark.django_db
# def test_CART030(client, setup_data):
#     """CART030: Kiểm tra lỗi khi 'mamau' là chuỗi trống"""
#     giohang = GioHang.objects.create(
#         KhachHang=setup_data['khachhang'],
#         SanPham=setup_data['sanpham'],
#         SoLuong=1,
#         MauSac=setup_data['mausac']
#     )
#     client.force_login(setup_data['user'])
#     response = client.post(reverse('update_color_cart'), {
#         'magiohang': giohang.id,
#         'mamau': ''
#     }, **{'HTTP_HOST': 'testserver'})
#     assert response.json() == {"error": "Vui Lòng Chọn Lại Màu!"}

# CART031
@pytest.mark.django_db
def test_CART031(client, setup_data):
    """CART031: Kiểm tra lỗi khi magiohang không tồn tại"""
    mausac_update = MauSac.objects.create(id=2, TenMauSac='Blue', MaMauSac='#0000FF')
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'magiohang': 999, # ID giỏ hàng không tồn tại
        'mamau': mausac_update.id
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Giỏ hàng không tồn tại!"}

# CART032
@pytest.mark.django_db
def test_CART032(client, setup_data):
    """CART032: Kiểm tra lỗi khi mamau không tồn tại"""
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    client.force_login(setup_data['user'])
    response = client.post(reverse('update_color_cart'), {
        'magiohang': giohang.id,
        'mamau': 999
    }, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Màu sắc không tồn tại!"}

# CART033
@pytest.mark.django_db
def test_CART033(client, setup_data):
    """CART035: Kiểm tra chuyển hướng khi không phải POST"""
    client.force_login(setup_data['user'])
    response = client.get(reverse('update_color_cart'), **{'HTTP_HOST': 'testserver'})
    assert response.url == reverse('cart_list')

# CART034
@pytest.mark.django_db
def test_CART034(client, setup_data):
    """CART034: Kiểm tra chuyển hướng khi user chưa đăng nhập"""
    response = client.get(reverse('delete_product_cart', args=[1]), **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Vui Lòng Đăng Nhập!"}

# CART035
@pytest.mark.django_db
def test_CART035(client, setup_data):
    """CART035: Đảm bảo xóa sản phẩm thành công"""
    giohang = GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=1,
        MauSac=setup_data['mausac']
    )
    client.force_login(setup_data['user'])
    response = client.get(reverse('delete_product_cart', args=[giohang.id]), **{'HTTP_HOST': 'testserver'})
    assert response.url == reverse('cart_list')
    assert not GioHang.objects.filter(id=giohang.id).exists()

# CART036
@pytest.mark.django_db
def test_CART036(client, setup_data):
    """CART036: Kiểm tra lỗi khi id không tồn tại"""
    client.force_login(setup_data['user'])
    response = client.get(reverse('delete_product_cart', args=[999]), **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Sản phẩm không tồn tại trong giỏ hàng!"}

# CART037
@pytest.mark.django_db
def test_CART037(client):
    """CART037: Kiểm tra trả về lỗi khi user chưa đăng nhập."""
    response = client.post(reverse('check_property_product'), {}, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Vui Lòng Đăng Nhập!"}

# CART038
@pytest.mark.django_db
def test_CART038(client, setup_data):
    """CART038: Đảm bảo giỏ hàng hợp lệ khi không có lỗi."""
    client.force_login(setup_data['user'])
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        MauSac=setup_data['mausac'],
        SoLuong=2
    )
    response = client.post(reverse('check_property_product'), {}, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"success": "Giỏ Hàng Hợp Lệ!"}

# CART039
@pytest.mark.django_db
def test_CART039(client, setup_data):
    """CART039: Kiểm tra lỗi khi giỏ hàng thiếu màu sắc."""
    client.force_login(setup_data['user'])
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=2,
        MauSac=None  # thiếu màu
    )
    response = client.post(reverse('check_property_product'), {}, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Vui Lòng Chọn Đủ Màu Sắc Cho Các Sản Phẩm!"}

# CART040
@pytest.mark.django_db
def test_CART040(client, setup_data):
    """CART040: Kiểm tra lỗi khi giỏ hàng có số lượng bằng 0."""
    client.force_login(setup_data['user'])
    GioHang.objects.create(
        KhachHang=setup_data['khachhang'],
        SanPham=setup_data['sanpham'],
        SoLuong=0,
        MauSac=setup_data['mausac']
    )
    response = client.post(reverse('check_property_product'), {}, **{'HTTP_HOST': 'testserver'})
    assert response.json() == {"error": "Số Lượng Sản Phẩm Phải Lớn Hơn 0!"}

# CART041
@pytest.mark.django_db
def test_CART041(client, setup_data):
    """CART041: Kiểm tra chuyển hướng khi không phải POST."""
    client.force_login(setup_data['user'])
    response = client.get(reverse('check_property_product'), **{'HTTP_HOST': 'testserver'})
    assert response.url == reverse('cart_list')