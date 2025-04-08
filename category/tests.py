import pytest
from django.urls import reverse
from product.models import ChuyenMuc, SanPham

# Fixture để tạo client
@pytest.fixture
def client():
    from django.test import Client
    return Client()

# Fixture để tạo dữ liệu mẫu cho Category
@pytest.fixture
def category_data(db):
    chuyenmuc1 = ChuyenMuc.objects.create(TenChuyenMuc="Chuyen Muc 1")  # DuongDan="chuyen-muc-1"
    chuyenmuc2 = ChuyenMuc.objects.create(TenChuyenMuc="Chuyen Muc 2")  # DuongDan="chuyen-muc-2"
    return chuyenmuc1, chuyenmuc2

# Fixture để tạo dữ liệu mẫu cho DetailCategory
@pytest.fixture
def detail_category_data(db):
    # Tạo ChuyenMuc với TenChuyenMuc="Test Category", DuongDan sẽ tự động thành "test-category"
    chuyenmuc = ChuyenMuc.objects.create(TenChuyenMuc="Test Category")
    for i in range(15):
        SanPham.objects.create(
            ChuyenMuc=chuyenmuc,
            TenSanPham=f"San Pham {i+1}",
            GiaBan=1000 * (i + 1),
            GiaKhuyenMai=1200 * (i + 1),
            id=i + 1
        )
    return chuyenmuc

# Test Case 1
def test_category_view_get_success(client, category_data):
    """
    Mục tiêu: Kiểm tra xem GET request tới Category view có trả về danh sách chuyên mục thành công không.
    Input: GET request tới URL '/chuyen-muc/'.
    Expected Output: HTTP 200, template 'category/list.html', dữ liệu chứa tất cả chuyên mục (2 chuyên mục).
    Ghi chú: Đảm bảo template được render với dữ liệu chính xác.
    """
    response = client.get(reverse('category'), HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.templates[0].name == 'category/list.html'
    assert len(response.context['chuyenmuc']) == 2
    assert response.context['title'] == "Chuyên Mục Sản Phẩm"

# Test Case 2
def test_category_view_exception(client, monkeypatch):
    """
    Mục tiêu: Kiểm tra xử lý ngoại lệ trong Category view khi có lỗi (giả lập lỗi truy vấn cơ sở dữ liệu).
    Input: GET request tới URL '/chuyen-muc/' với mock lỗi database.
    Expected Output: Ném ngoại lệ Exception (vì view crash khi render 404error.html).
    Ghi chú: Không thể mong đợi HTTP 200 vì context processor hoặc template gọi lại ChuyenMuc.objects.all(), 
             mà không thể mock hoàn toàn do hạn chế không sửa code gốc.
    """
    def mock_all():
        raise Exception("Database error")
    
    # Mock ChuyenMuc.objects.all()
    monkeypatch.setattr(ChuyenMuc.objects, 'all', mock_all)
    
    # Thử mock context processor (dù có thể không đủ nếu template gọi trực tiếp)
    def mock_context_processor(request):
        return {'chuyenmuc_load': []}
    monkeypatch.setattr('website.context_processors.category_context_processor', mock_context_processor)
    
    # Kiểm tra ngoại lệ thay vì response
    with pytest.raises(Exception, match="Database error"):
        client.get(reverse('category'), HTTP_HOST='testserver')

# Test Case 3
def test_detail_category_no_slug_redirect(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra xem nếu slug không hợp lệ thì trả về 404.
    Input: GET request tới '/none/' (slug không hợp lệ).
    Expected Output: HTTP 404.
    Ghi chú: View hiện tại trả về 404 thay vì redirect.
    """
    response = client.get('/none/', HTTP_HOST='testserver')
    assert response.status_code == 404

# Test Case 4
def test_detail_category_valid_slug_first_page(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra xem GET request với slug hợp lệ có trả về trang đầu tiên đúng không.
    Input: GET request tới '/chuyen-muc/test-category/'.
    Expected Output: HTTP 200, template 'category/product.html', 12 sản phẩm đầu tiên.
    Ghi chú: Đảm bảo phân trang mặc định hoạt động và trả về đúng số lượng sản phẩm.
    """
    response = client.get(reverse('detail_category', args=['test-category']), HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.templates[0].name == 'category/product.html'
    assert len(response.context['sanpham']) == 12
    assert response.context['page'] == 1
    assert response.context['title'] == "Chuyên Mục Test Category"

# Test Case 5
def test_detail_category_pagination_second_page(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra phân trang khi truy cập trang thứ 2.
    Input: GET request tới '/chuyen-muc/test-category/?trang=2'.
    Expected Output: HTTP 200, template 'category/product.html', 3 sản phẩm (phần còn lại).
    Ghi chú: Với 15 sản phẩm và 12 sản phẩm/trang, trang 2 sẽ có 3 sản phẩm.
    """
    response = client.get(reverse('detail_category', args=['test-category']) + '?trang=2', HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.templates[0].name == 'category/product.html'
    assert len(response.context['sanpham']) == 3
    assert response.context['page'] == 2

# Test Case 6
def test_detail_category_invalid_page(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra xử lý khi truy cập trang không hợp lệ (vượt quá số trang).
    Input: GET request tới '/chuyen-muc/test-category/?trang=3'.
    Expected Output: HTTP 200, template '404error.html'.
    Ghi chú: Với 15 sản phẩm, chỉ có 2 trang, nên trang 3 sẽ gây lỗi.
    """
    response = client.get(reverse('detail_category', args=['test-category']) + '?trang=3', HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.templates[0].name == '404error.html'

# Test Case 7
def test_detail_category_sort_descending(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra sắp xếp sản phẩm theo giá giảm dần.
    Input: GET request tới '/chuyen-muc/test-category/?sap_xep=giam'.
    Expected Output: HTTP 200, sản phẩm đầu tiên có giá cao nhất (15000).
    Ghi chú: Đảm bảo sắp xếp theo '-GiaBan' hoạt động.
    """
    response = client.get(reverse('detail_category', args=['test-category']) + '?sap_xep=giam', HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.context['sanpham'][0].GiaBan == 15000

# Test Case 8
def test_detail_category_sort_ascending(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra sắp xếp sản phẩm theo giá tăng dần.
    Input: GET request tới '/chuyen-muc/test-category/?sap_xep=tang'.
    Expected Output: HTTP 200, sản phẩm đầu tiên có giá thấp nhất (1000).
    Ghi chú: Đảm bảo sắp xếp theo 'GiaBan' hoạt động.
    """
    response = client.get(reverse('detail_category', args=['test-category']) + '?sap_xep=tang', HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.context['sanpham'][0].GiaBan == 1000

# Test Case 9
def test_detail_category_sort_newest(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra sắp xếp sản phẩm theo thứ tự mới nhất (id giảm dần).
    Input: GET request tới '/chuyen-muc/test-category/?sap_xep=moi'.
    Expected Output: HTTP 200, sản phẩm đầu tiên có id cao nhất (15).
    Ghi chú: Đảm bảo sắp xếp theo '-id' hoạt động.
    """
    response = client.get(reverse('detail_category', args=['test-category']) + '?sap_xep=moi', HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response.context['sanpham'][0].id == 15

# Test Case 10
def test_detail_category_invalid_slug(client, detail_category_data):
    """
    Mục tiêu: Kiểm tra xử lý khi slug không tồn tại.
    Input: GET request tới '/chuyen-muc/invalid-slug/'.
    Expected Output: Ném ngoại lệ ChuyenMuc.DoesNotExist (vì view không xử lý lỗi).
    Ghi chú: View hiện tại crash khi slug không tồn tại, không trả về 404error.html.
    """
    with pytest.raises(ChuyenMuc.DoesNotExist):
        client.get(reverse('detail_category', args=['invalid-slug']), HTTP_HOST='testserver')

# def test_category_view_empty_data(client):
#     """
#     Mục tiêu: Kiểm tra hành vi của Category view khi không có dữ liệu ChuyenMuc.
#     Input: GET request tới URL '/chuyen-muc/' với cơ sở dữ liệu rỗng.
#     Expected Output: HTTP 200, template 'category/list.html', danh sách chuyên mục rỗng.
#     Ghi chú: Đảm bảo view xử lý trường hợp không có dữ liệu mà không crash.
#     """
#     response = client.get(reverse('category'), HTTP_HOST='testserver')
#     assert response.status_code == 200
#     assert response.templates[0].name == 'category/list.html'
#     assert len(response.context['chuyenmuc']) == 0
# def test_detail_category_empty_products(client, db):
#     """
#     Mục tiêu: Kiểm tra hành vi của DetailCategory view khi chuyên mục không có sản phẩm.
#     Input: GET request tới '/chuyen-muc/test-category/' với chuyên mục rỗng.
#     Expected Output: HTTP 200, template 'category/product.html', danh sách sản phẩm rỗng.
#     Ghi chú: Đảm bảo view xử lý trường hợp chuyên mục không có sản phẩm.
#     """
#     ChuyenMuc.objects.create(TenChuyenMuc="Test Category")  # DuongDan="test-category"
#     response = client.get(reverse('detail_category', args=['test-category']), HTTP_HOST='testserver')
#     assert response.status_code == 200
#     assert response.templates[0].name == 'category/product.html'
#     assert len(response.context['sanpham']) == 0
# def test_detail_category_invalid_sort_param(client, detail_category_data):
#     """
#     Mục tiêu: Kiểm tra hành vi của DetailCategory view khi tham số sắp xếp không hợp lệ.
#     Input: GET request tới '/chuyen-muc/test-category/?sap_xep=invalid'.
#     Expected Output: HTTP 200, template 'category/product.html', 12 sản phẩm đầu tiên với sắp xếp mặc định.
#     Ghi chú: Đảm bảo view xử lý tham số không hợp lệ bằng cách dùng sắp xếp mặc định.
#     """
#     response = client.get(reverse('detail_category', args=['test-category']) + '?sap_xep=invalid', HTTP_HOST='testserver')
#     assert response.status_code == 200
#     assert response.templates[0].name == 'category/product.html'
#     assert len(response.context['sanpham']) == 12
#     assert response.context['page'] == 1
# def test_detail_category_pagination_negative_page(client, detail_category_data):
#     """
#     Mục tiêu: Kiểm tra hành vi của DetailCategory view khi tham số trang là số âm.
#     Input: GET request tới '/chuyen-muc/test-category/?trang=-1'.
#     Expected Output: HTTP 200, template 'category/product.html', 12 sản phẩm đầu tiên (trang 1).
#     Ghi chú: Đảm bảo view xử lý trang âm bằng cách mặc định về trang 1.
#     """
#     response = client.get(reverse('detail_category', args=['test-category']) + '?trang=-1', HTTP_HOST='testserver')
#     assert response.status_code == 200
#     assert response.templates[0].name == 'category/product.html'
#     assert len(response.context['sanpham']) == 12
#     assert response.context['page'] == 1
# def test_detail_category_slug_case_insensitivity(client, detail_category_data):
#     """
#     Mục tiêu: Kiểm tra xem DetailCategory view có xử lý slug không phân biệt chữ hoa/thường không.
#     Input: GET request tới '/chuyen-muc/TEST-CATEGORY/'.
#     Expected Output: HTTP 200, template 'category/product.html', 12 sản phẩm đầu tiên.
#     Ghi chú: Đảm bảo slug không phân biệt hoa/thường trong truy vấn.
#     """
#     response = client.get(reverse('detail_category', args=['TEST-CATEGORY']), HTTP_HOST='testserver')
#     assert response.status_code == 200
#     assert response.templates[0].name == 'category/product.html'
#     assert len(response.context['sanpham']) == 12
#     assert response.context['page'] == 1