function showTab(tabId, element) {
    // Скрываем все табы
    var tabs = document.getElementsByClassName('tab-content');
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.remove('active-tab');
    }

    // Убираем активный класс со всех вкладок
    var tabLinks = document.getElementsByClassName('tab-link');
    for (var i = 0; i < tabLinks.length; i++) {
      tabLinks[i].classList.remove('active-tab-link');
    }

    // Показываем выбранный таб
    var selectedTab = document.getElementById(tabId);
    if (selectedTab) {
      selectedTab.classList.add('active-tab');
    }

    // Добавляем активный класс к выбранной вкладке
    element.classList.add('active-tab-link');
  }

const numItemsToShow = 6;
const serviceItems = document.querySelectorAll('.flex-wrap > .p-4');
let numPages = Math.ceil(serviceItems.length / numItemsToShow);
let currentPage = 0;

function showPage(page) {
  serviceItems.forEach((item, index) => {
    item.style.display = 'none';
    if (index >= page * numItemsToShow && index < (page + 1) * numItemsToShow) {
      item.style.display = 'block';
    }
  });
}

function setupPagination() {
  const prevPageButton = document.getElementById('prevPage');
  const nextPageButton = document.getElementById('nextPage');
  const paginationPageInput = document.getElementById('PaginationPage');

  // Обновленный код для управления видимостью пагинации и формы
  if (numPages <= 1) {
    // Если всего одна страница или вовсе нет страниц, скрываем пагинацию и форму
    prevPageButton.style.display = 'none';
    nextPageButton.style.display = 'none';
    paginationPageInput.style.display = 'none';
  } else {
    // Иначе показываем пагинацию и форму
    prevPageButton.style.display = 'inline-block';
    nextPageButton.style.display = 'inline-block';
    paginationPageInput.style.display = 'inline-block';
  }

  prevPageButton.addEventListener('click', (event) => {
    event.preventDefault();
    if (currentPage > 0) {
      currentPage--;
      showPage(currentPage);
      paginationPageInput.value = currentPage + 1;
    }
  });

  nextPageButton.addEventListener('click', (event) => {
    event.preventDefault();
    if (currentPage < numPages - 1) {
      currentPage++;
      showPage(currentPage);
      paginationPageInput.value = currentPage + 1;
    }
  });
}

showPage(currentPage);
setupPagination();
document.getElementById('PaginationPage').value = currentPage + 1;


document.addEventListener('DOMContentLoaded', function () {
  const descriptionContainers = document.querySelectorAll('.description-container');

  descriptionContainers.forEach(container => {
    const originalText = container.innerText;
    const showMoreLink = document.createElement('span');
    showMoreLink.classList.add('show-more');
    showMoreLink.innerText = 'Показать больше';
    showMoreLink.addEventListener('click', () => {
      container.innerText = originalText;
    });

    if (container.scrollHeight > container.clientHeight) {
      container.appendChild(showMoreLink);
    }
  });
});


