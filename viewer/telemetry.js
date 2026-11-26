(function () {
  'use strict';

  const ns = 'http://www.w3.org/2000/svg';
  const ink = '#253039';
  const axis = '#747a7c';
  const cursorInk = '#933d28';
  const numbers = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 });
  const metrics = {
    altitude: { name: 'Höhe', symbol: 'z', unit: 'm', axisUnit: 'm', read: s => s.z, zero: true },
    speed: { name: 'Geschwindigkeit', symbol: 'v', unit: 'm/s', axisUnit: '(m/s)', read: s => Math.hypot(s.vx, s.vz), zero: true },
    mass: { name: 'Masse', symbol: 'm', unit: 'kg', axisUnit: 'kg', read: s => s.m, zero: false }
  };

  function element(parent, name, attributes, text) {
    const child = document.createElementNS(ns, name);
    for (const [key, value] of Object.entries(attributes)) child.setAttribute(key, value);
    if (text !== undefined) child.textContent = text;
    parent.appendChild(child);
    return child;
  }

  function tickStep(raw) {
    const power = 10 ** Math.floor(Math.log10(raw));
    const choices = [1, 2, 2.5, 5, 10].map(size => size * power);
    return choices.reduce((best, step) =>
      Math.abs(Math.log(step / raw)) < Math.abs(Math.log(best / raw)) ? step : best
    );
  }

  function verticalScale(samples, metric, top, bottom) {
    let lo = Infinity;
    let hi = -Infinity;
    for (const sample of samples) {
      const value = metric.read(sample);
      lo = Math.min(lo, value);
      hi = Math.max(hi, value);
    }
    if (metric.zero) lo = Math.min(0, lo);
    const intervals = Math.max(2, Math.min(5, (bottom - top) / 27));
    const step = tickStep((hi - lo || 1) / intervals);
    // Include small negative excursions in the trace while keeping the ground tick at zero.
    const min = metric.zero && lo > -step * 0.05 ? lo : Math.floor(lo / step) * step;
    const max = Math.max(min + step, Math.ceil(hi / step) * step);
    return { min, max, step, y: value => bottom - (value - min) * (bottom - top) / (max - min) };
  }

  function create(container, flight, onSeek) {
    const { samples, duration } = flight;
    const svg = element(container, 'svg', {
      width: '100%', height: '100%', role: 'slider', tabindex: 0,
      'aria-label': 'Flugzeit im Zeitdiagramm', 'aria-orientation': 'horizontal',
      'aria-valuemin': 0, 'aria-valuemax': duration, fill: ink,
      'font-family': 'Cambria, Georgia, serif', 'font-size': 12
    });
    svg.style.cssText = 'display:block;touch-action:pan-y;cursor:crosshair;outline-offset:2px;font-variant-numeric:tabular-nums';
    const figure = element(svg, 'g', { 'aria-hidden': 'true' });
    const left = 35;
    let width = 0, height = 0, right = 0;
    let selection = 'all', time = 0, sample = samples[0], pointer = null;
    let panels = [];

    function x(t) { return left + t / duration * (right - left); }

    function draw() {
      figure.replaceChildren();
      panels = [];
      if (width < 100 || height < 100) return;
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      right = width - 13;
      const selected = selection === 'all' ? Object.values(metrics) : [metrics[selection]];
      const gap = 10;
      const rowHeight = (height - 37 - gap * (selected.length - 1)) / selected.length;
      const timeStep = tickStep(duration / Math.max(3, Math.min(8, (right - left) / 52)));

      for (const [index, metric] of selected.entries()) {
        const rowStart = 2 + index * (rowHeight + gap);
        const top = rowStart + 18;
        const bottom = rowStart + rowHeight;
        const scale = verticalScale(samples, metric, top, bottom);
        const group = element(figure, 'g', { 'data-series': metric.symbol });
        const heading = element(group, 'text', { x: left, y: rowStart + 11, 'font-size': 13 });
        element(heading, 'tspan', { 'font-weight': 600 }, metric.name);
        const variable = { 'font-family': 'Georgia, serif', 'font-style': 'italic', 'font-size': 13 };
        element(heading, 'tspan', { ...variable, dx: 7 }, metric.symbol);
        element(heading, 'tspan', {}, ' / ' + metric.axisUnit);

        for (let i = Math.ceil(scale.min / scale.step); i <= Math.floor(scale.max / scale.step); i++) {
          const value = i * scale.step;
          const py = scale.y(value);
          if (py < bottom - 1) element(group, 'line', { x1: left, x2: right, y1: py, y2: py, stroke: '#e5e6e3', 'stroke-width': 0.7 });
          element(group, 'path', { d: `M${left - 3} ${py}h3`, stroke: axis, fill: 'none' });
          element(group, 'text', { x: left - 6, y: py + 3, 'text-anchor': 'end' }, numbers.format(value || 0));
        }

        element(group, 'path', { d: `M${left} ${top}V${bottom}H${right}`, fill: 'none', stroke: axis, 'stroke-width': 0.85 });
        for (let i = 0; i * timeStep <= duration; i++) {
          const t = i * timeStep;
          const px = x(t);
          element(group, 'path', { d: `M${px} ${bottom}v3`, stroke: axis, 'stroke-width': 0.85 });
          if (index === selected.length - 1) {
            element(group, 'text', { x: px, y: bottom + 14, 'text-anchor': 'middle' }, numbers.format(t));
          }
        }

        const path = samples.map((s, i) =>
          `${i ? 'L' : 'M'}${x(s.t).toFixed(2)},${scale.y(metric.read(s)).toFixed(2)}`
        ).join(' ');
        element(group, 'path', { d: path, fill: 'none', stroke: ink, 'stroke-width': 1.65, 'stroke-linejoin': 'round' });
        const cursor = element(group, 'line', { y1: top, y2: bottom, stroke: cursorInk, 'stroke-width': 0.85, 'stroke-dasharray': '3 3' });
        const mark = element(group, 'rect', { width: 3.6, height: 3.6, fill: cursorInk });
        panels.push({ metric, y: scale.y, cursor, mark });
      }

      const caption = element(figure, 'text', { x: (left + right) / 2, y: height - 4, 'text-anchor': 'middle', 'font-size': 11 });
      element(caption, 'tspan', {}, 'Zeit ');
      element(caption, 'tspan', { 'font-family': 'Georgia, serif', 'font-style': 'italic', 'font-size': 13 }, 't');
      element(caption, 'tspan', {}, ' / s');
    }

    function positionCursor() {
      const px = x(time);
      const values = [`${numbers.format(time)} Sekunden`];
      for (const { metric, y, cursor, mark } of panels) {
        const value = metric.read(sample);
        cursor.setAttribute('x1', px);
        cursor.setAttribute('x2', px);
        mark.setAttribute('x', px - 1.8);
        mark.setAttribute('y', y(value) - 1.8);
        values.push(`${metric.name} ${numbers.format(value)} ${metric.unit}`);
      }
      svg.setAttribute('aria-valuenow', time.toFixed(2));
      svg.setAttribute('aria-valuetext', values.join(', '));
    }

    function update(t, nextSample, nextSelection = 'all') {
      time = Math.max(0, Math.min(duration, t));
      sample = nextSample;
      if (selection !== nextSelection) {
        selection = nextSelection;
        draw();
      }
      positionCursor();
    }

    function resize() {
      const bounds = svg.getBoundingClientRect();
      const w = Math.round(bounds.width), h = Math.round(bounds.height);
      if (w === width && h === height) return;
      width = w;
      height = h;
      draw();
      positionCursor();
    }

    function seekPointer(event) {
      const bounds = svg.getBoundingClientRect();
      if (!bounds.width || right <= left) return;
      const px = (event.clientX - bounds.left) * width / bounds.width;
      onSeek(duration * Math.max(0, Math.min(1, (px - left) / (right - left))));
    }
    svg.addEventListener('pointerdown', event => {
      if (event.button !== 0 || pointer !== null) return;
      pointer = event.pointerId;
      svg.setPointerCapture(pointer);
      seekPointer(event);
    });
    svg.addEventListener('pointermove', event => { if (event.pointerId === pointer) seekPointer(event); });
    svg.addEventListener('lostpointercapture', event => { if (event.pointerId === pointer) pointer = null; });
    svg.addEventListener('keydown', event => {
      const step = event.shiftKey ? 1 : 0.25;
      const targets = { ArrowLeft: time - step, ArrowRight: time + step, ArrowDown: time - step, ArrowUp: time + step,
        PageDown: time - duration / 10, PageUp: time + duration / 10, Home: 0, End: duration };
      if (!Object.hasOwn(targets, event.key)) return;
      event.preventDefault();
      event.stopPropagation();
      onSeek(Math.max(0, Math.min(duration, targets[event.key])));
    });
    resize();
    if (window.ResizeObserver) new ResizeObserver(resize).observe(svg);
    else window.addEventListener('resize', resize);
    return { update };
  }

  window.FlightTelemetry = { create };
})();
