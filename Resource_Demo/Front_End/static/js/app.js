const grid = document.getElementById('bookGrid');
const search = document.getElementById('searchInput');
const category = document.getElementById('categorySelect');
const clear = document.getElementById('clearButton');
const resultCount = document.getElementById('resultCount');
const empty = document.getElementById('emptyState');
const error = document.getElementById('errorState');
let books = [];
const escapeHTML = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render() {
  const q = search.value.trim().toLocaleLowerCase();
  const selected = category.value;
  const matches = books.filter(b => (!selected || b.category === selected) &&
    [b.title,b.author,b.description].some(v => String(v).toLocaleLowerCase().includes(q)));
  resultCount.textContent = `${matches.length} of ${books.length} books`;
  empty.hidden = matches.length !== 0;
  grid.innerHTML = matches.map(b => `<article class="book-card">
    <div class="cover"><img loading="lazy" src="${escapeHTML(b.cover)}" alt="Cover artwork for ${escapeHTML(b.title)}"></div>
    <span class="category">${escapeHTML(b.category)}</span>
    <h3>${escapeHTML(b.title)}</h3><p class="author">by ${escapeHTML(b.author)}</p>
    <p class="book-desc">${escapeHTML(b.description)}</p>
    <div class="book-meta"><span class="price">$${Number(b.price).toFixed(2)}</span><span class="stock ${b.stock === 0 ? 'out' : ''}">${b.stock === 0 ? 'Out of stock' : `${b.stock} in stock`}</span></div>
  </article>`).join('');
}
async function init() {
  try {
    const response = await fetch('/api/books');
    if (!response.ok) throw new Error('API request failed');
    const data = await response.json();
    books = data.books;
    [...new Set(books.map(b => b.category))].sort().forEach(c => {
      const option = document.createElement('option'); option.value = c; option.textContent = c;
      category.appendChild(option);
    });
    render();
  } catch (e) { resultCount.textContent = 'Unavailable'; error.hidden = false; console.error(e); }
}
search.addEventListener('input', render);
category.addEventListener('change', render);
clear.addEventListener('click', () => { search.value = ''; category.value = ''; render(); search.focus(); });
init();
