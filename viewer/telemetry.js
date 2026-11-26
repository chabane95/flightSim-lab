(function () {
  'use strict';

  const ns = 'http://www.w3.org/2000/svg';
  const ink = '#087e77';
  const labels = '#566a73';
  const numbers = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 });
  const metrics = {
    altitude: { name: 'Höhe', unit: 'm', read: s => s.z, zero: true },
    speed: { name: 'Geschwindigkeit', unit: 'm/s', read: s => Math.hypot(s.vx, s.vz), zero: true },
    mass: { name: 'Masse', unit: 'kg', read: s => s.m, zero: false }
  };
  let nextId = 0;

  function element(name, attributes, parent) {
    const item = document.createElementNS(ns, name);
    for (const [key, value] of Object.entries(attributes)) item.setAttribute(key, value);
    parent.appendChild(item);
    return item;
  }

  function tickStep(raw) {
    const power = 10 ** Math.floor(Math.log10(raw));
    const fraction = raw / power;
    const step = [1, 2, 2.5, 5, 10].find(candidate => candidate >= fraction);
    return step * power;
  }

  function create(container, flight, onSeek) {
    const { samples, duration } = flight;
    const gradientId = `telemetry-area-${++nextId}`;
    const svg = element('svg', {
      role: 'slider', tabindex: 0, 'aria-valuemin': 0, 'aria-valuemax': duration,
      'aria-label': 'Flugzeit im Telemetriediagramm', 'aria-orientation': 'horizontal',
      'font-family': 'ui-monospace, SFMono-Regular, Consolas, monospace', 'font-size': 10
    }, container);
    svg.style.cssText = 'display:block;width:100%;height:148px;touch-action:pan-y;cursor:crosshair;outline-offset:2px';

    const defs = element('defs', {}, svg);
    const gradient = element('linearGradient', { id: gradientId, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    element('stop', { offset: '0%', 'stop-color': ink, 'stop-opacity': 0.2 }, gradient);
    element('stop', { offset: '100%', 'stop-color': ink, 'stop-opacity': 0.025 }, gradient);
    const guides = element('g', { 'aria-hidden': 'true' }, svg);
    const area = element('path', { fill: `url(#${gradientId})` }, svg);
    const line = element('path', { stroke: ink, 'stroke-width': 2, fill: 'none', 'stroke-linejoin': 'round' }, svg);
    const cursor = element('line', { stroke: '#547d7a', 'stroke-width': 1, 'stroke-dasharray': '3 3' }, svg);
    const dot = element('circle', { fill: ink, stroke: '#ffffff', 'stroke-width': 2, r: 4 }, svg);

    const height = 148;
    const left = 39;
    const top = 20;
    const bottom = height - 24;
    let right;
    let yMin;
    let yMax;
    let metric;
    let width;
    let time = 0;
    let currentSample = samples[0];
    let pointer = null;

    function x(t) { return left + t / duration * (right - left); }
    function y(value) { return bottom - (value - yMin) / (yMax - yMin) * (bottom - top); }

    function label(position, value) {
      element('text', { fill: labels, ...position }, guides).textContent = value;
    }

    function drawChart() {
      right = width - 16;
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      guides.replaceChildren();
      const { read, unit, zero } = metrics[metric];
      let lo = Infinity;
      let hi = -Infinity;
      for (const sample of samples) {
        const value = read(sample);
        lo = Math.min(lo, value);
        hi = Math.max(hi, value);
      }
      if (zero) lo = Math.min(0, lo);
      const step = tickStep((hi - lo || 1) / 4);
      // Preserve small excursions below zero without adding an entire empty tick interval.
      yMin = zero && lo > -step * 0.05 ? lo : Math.floor(lo / step) * step;
      yMax = Math.max(yMin + step, Math.ceil(hi / step) * step);

      label({ x: left - 9, y: 10, 'text-anchor': 'end' }, unit);
      for (let i = Math.ceil(yMin / step); i <= Math.floor(yMax / step); i++) {
        const value = i * step;
        const py = y(value);
        element('line', { x1: left, x2: right, y1: py, y2: py, stroke: py < bottom - 1 ? '#dce5e6' : '#b5c5c7' }, guides);
        label({ x: left - 9, y: py + 3, 'text-anchor': 'end' }, numbers.format(value || 0));
      }

      const timeStep = tickStep(duration / Math.max(3, Math.min(8, Math.floor((right - left) / 48))));
      for (let i = 0; i * timeStep <= duration; i++) {
        const t = i * timeStep;
        const px = x(t);
        element('line', { x1: px, x2: px, y1: bottom, y2: bottom + 4, stroke: '#b5c5c7' }, guides);
        label({ x: px, y: bottom + 17, 'text-anchor': 'middle' }, `${numbers.format(t)} s`);
      }

      const path = samples.map((s, i) => `${i ? 'L' : 'M'}${x(s.t).toFixed(2)},${y(read(s)).toFixed(2)}`).join(' ');
      line.setAttribute('d', path);
      area.setAttribute('d', `${path} L${x(samples[samples.length - 1].t)},${bottom} L${x(samples[0].t)},${bottom} Z`);
    }

    function update(t, sample, nextMetric) {
      time = Math.max(0, Math.min(duration, t));
      currentSample = sample;
      if (metric !== nextMetric || width === undefined) {
        metric = nextMetric;
        width = Math.max(90, Math.round(svg.getBoundingClientRect().width));
        drawChart();
      }
      const { read, name, unit } = metrics[metric];
      const px = x(time);
      const value = read(sample);
      cursor.setAttribute('x1', px);
      cursor.setAttribute('x2', px);
      cursor.setAttribute('y1', top);
      cursor.setAttribute('y2', bottom);
      dot.setAttribute('cx', px);
      dot.setAttribute('cy', y(value));
      svg.setAttribute('aria-valuenow', time.toFixed(2));
      svg.setAttribute('aria-valuetext', `${numbers.format(time)} Sekunden, ${name} ${numbers.format(value)} ${unit}`);
    }

    function seekPointer(event) {
      const bounds = svg.getBoundingClientRect();
      if (!bounds.width) return;
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
      if (!(event.key in targets)) return;
      event.preventDefault();
      event.stopPropagation();
      onSeek(Math.max(0, Math.min(duration, targets[event.key])));
    });

    update(0, currentSample, 'altitude');
    const resize = () => {
      const nextWidth = Math.max(90, Math.round(svg.getBoundingClientRect().width));
      if (width === nextWidth) return;
      width = nextWidth;
      drawChart();
      update(time, currentSample, metric);
    };
    if (window.ResizeObserver) new ResizeObserver(resize).observe(container);
    else window.addEventListener('resize', resize);
    return { update };
  }

  window.FlightTelemetry = { create };
})();
