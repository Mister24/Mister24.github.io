/* 日报赛道筛选 */
(function () {
  var tabs = document.querySelectorAll('.cat');
  if (!tabs.length) return;
  var items = document.querySelectorAll('[data-t]');
  var empty = document.querySelector('.empty');
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      tabs.forEach(function (x) { x.classList.remove('on'); });
      t.classList.add('on');
      var v = t.getAttribute('data-f'), n = 0;
      items.forEach(function (el) {
        var hit = (v === 'all' || el.getAttribute('data-t') === v);
        el.style.display = hit ? '' : 'none';
        if (hit) n += 1;
      });
      if (empty) empty.style.display = n ? 'none' : 'block';
    });
  });
})();

/* 代码块一键复制 */
(function () {
  document.querySelectorAll('figure.code').forEach(function (fig) {
    var btn = fig.querySelector('.copy');
    var code = fig.querySelector('code');
    if (!btn || !code) return;
    btn.addEventListener('click', function () {
      var text = code.innerText;
      var done = function () {
        btn.textContent = 'copied';
        btn.classList.add('done');
        setTimeout(function () { btn.textContent = 'copy'; btn.classList.remove('done'); }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done);
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });
})();

/* 目录高亮当前小节 */
(function () {
  var links = document.querySelectorAll('.toc a');
  if (!links.length) return;
  var map = {};
  links.forEach(function (a) {
    var el = document.getElementById(a.getAttribute('href').slice(1));
    if (el) map[el.id] = a;
  });
  var ids = Object.keys(map);
  if (!ids.length) return;
  window.addEventListener('scroll', function () {
    var cur = ids[0];
    ids.forEach(function (id) {
      if (document.getElementById(id).getBoundingClientRect().top < 120) cur = id;
    });
    links.forEach(function (a) { a.classList.remove('on'); });
    if (map[cur]) map[cur].classList.add('on');
  }, { passive: true });
})();
