import pytest
from django.urls import reverse
from news.models import TinTuc
from product.models import ChuyenMuc
from website.models import BannerMid
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


@pytest.fixture
def client():
    from django.test import Client
    return Client()

@pytest.fixture
def setup_data(db):
    # Tạo chuyên mục
    chuyenmuc = ChuyenMuc.objects.create(TenChuyenMuc="Âm Nhạc Hàn Quốc")

    # Tạo banner
    BannerMid.objects.create(
        HinhAnh=SimpleUploadedFile("banner.jpg", b"file_content"),
        ChuyenMuc=chuyenmuc,
        HienThi=True
    )

    # Tạo 12 bài viết tin tức
    for i in range(12):
        TinTuc.objects.create(
            TieuDe=f"Bài viết {i + 1}",
            AnhChinh=SimpleUploadedFile("image.jpg", b"file_content"),
            The="Giải trí",
            NoiDung="Nội dung bài viết...",
            created_at=timezone.now()
        )


def test_list_news_default(client, setup_data):
    """
    Mục tiêu: Kiểm tra xem khi không truyền tham số, view trả về đúng 8 bài viết đầu tiên và có phân trang.
    """
    url = reverse('list_news')
    response = client.get(url)
    assert response.status_code == 200
    assert response.templates[0].name == 'news/list.html'
    assert len(response.context['tintuc']) == 8
    assert response.context['page'] == 1
    assert response.context['len_page_count'] == 2  # 12 bài / 8 bài mỗi trang => 2 trang


def test_list_news_pagination_page_2(client, setup_data):
    """
    Mục tiêu: Kiểm tra phân trang - trang 2 hiển thị đúng bài viết còn lại.
    """
    url = reverse('list_news') + '?trang=2'
    response = client.get(url)
    assert response.status_code == 200
    assert response.templates[0].name == 'news/list.html'
    assert response.context['page'] == 2
    assert len(response.context['tintuc']) == 4  # 12 - 8 = 4 bài còn lại


def test_list_news_pagination_invalid_page(client, setup_data):
    """
    Mục tiêu: Kiểm tra khi truyền số trang không hợp lệ (quá lớn).
    """
    url = reverse('list_news') + '?trang=999'
    response = client.get(url)
    assert response.status_code == 200
    assert '404error.html' in [t.name for t in response.templates]


def test_list_news_search(client, setup_data):
    """
    Mục tiêu: Kiểm tra tính năng tìm kiếm tiêu đề.
    """
    url = reverse('list_news') + '?s=Bài viết 1'
    response = client.get(url)
    assert response.status_code == 200
    assert response.templates[0].name == 'news/list.html'
    assert any("Bài viết 1" in item.TieuDe for item in response.context['tintuc'])

def test_list_news_no_results(client, setup_data):
    """
    Mục tiêu: Kiểm tra khi không có kết quả tìm kiếm phù hợp.
    """
    url = reverse('list_news') + '?s=khongtonTai'
    response = client.get(url)
    assert response.status_code == 200
    assert response.templates[0].name == 'news/list.html'
    assert len(response.context['tintuc']) == 0


def test_list_news_negative_page(client, setup_data):
    """
    Mục tiêu: Kiểm tra khi người dùng nhập số trang âm.
    """
    url = reverse('list_news') + '?trang=-1'
    response = client.get(url)
    assert response.status_code == 200
    assert '404error.html' in [t.name for t in response.templates]


def test_list_news_non_integer_page(client, setup_data):
    """
    Mục tiêu: Kiểm tra khi số trang không phải số nguyên.
    """
    url = reverse('list_news') + '?trang=abc'
    response = client.get(url)
    assert response.status_code == 200
    assert '404error.html' in [t.name for t in response.templates]


def test_list_news_combined_search_and_page(client, setup_data):
    """
    Mục tiêu: Kiểm tra kết hợp tìm kiếm và phân trang.
    """
    url = reverse('list_news') + '?s=Bài viết&trang=1'
    response = client.get(url)
    assert response.status_code == 200
    assert response.templates[0].name == 'news/list.html'
    assert len(response.context['tintuc']) <= 8
    assert all("Bài viết" in item.TieuDe for item in response.context['tintuc'])


# ✅ Test Case 1: Truy cập bài viết thành công
@pytest.mark.django_db
def test_detail_news_success(client, setup_data):
    tintuc = TinTuc.objects.all()[2]
    response = client.get(reverse('detail_news', args=[tintuc.DuongDan]))

    assert response.status_code == 200
    assert response.templates[0].name == 'news/detail.html'
    assert 'tintuc' in response.context
    assert response.context['tintuc'].id == tintuc.id

# ✅ Test Case 2: Truy cập bài viết không tồn tại
@pytest.mark.django_db
def test_detail_news_not_found(client, setup_data):
    response = client.get(reverse('detail_news', args=['khong-ton-tai']))
    assert response.status_code == 200
    assert response.templates[0].name == '404error.html'

# ✅ Test Case 3: Bài viết đầu tiên (prev = chính nó)
@pytest.mark.django_db
def test_detail_news_first_item(client, setup_data):
    first_news = TinTuc.objects.order_by("id").first()
    response = client.get(reverse('detail_news', args=[first_news.DuongDan]))

    assert response.status_code == 200
    assert response.context['prev_news'].id == first_news.id
    assert response.context['next_news'].id == first_news.id + 1

# ✅ Test Case 4: Bài viết cuối cùng (next = chính nó)
@pytest.mark.django_db
def test_detail_news_last_item(client, setup_data):
    last_news = TinTuc.objects.order_by("-id").first()
    response = client.get(reverse('detail_news', args=[last_news.DuongDan]))

    assert response.status_code == 200
    assert response.context['next_news'].id == last_news.id
    assert response.context['prev_news'].id == last_news.id - 1