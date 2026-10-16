(function () {
  var tabs = document.querySelectorAll('.cat');
  var items = document.querySelectorAll('[data-t]');
  var empty = document.querySelector('.empty');
  if (!tabs.length) return;
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
