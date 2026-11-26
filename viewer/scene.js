/* The scene projects the solver's horizontal position and altitude onto metric axes. */
(() => {
  'use strict';

  const ns = 'http://www.w3.org/2000/svg';
  const ink = '#272925';
  const muted = '#5c5e58';
  const current = '#b33f29';
  const serif = 'Georgia, "Times New Roman", serif';
  const number = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 });
  let sceneId = 0;

  function element(parent, tag, attrs = {}, content) {
    const node = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (content !== undefined) node.textContent = content;
    parent.appendChild(node);
    return node;
  }

  function tickStep(span, count) {
    const ideal = span / Math.max(2, count);
    const magnitude = 10 ** Math.floor(Math.log10(ideal));
    const choices = [1, 2, 2.5, 5, 10].map(value => value * magnitude);
    return choices.reduce((best, step) =>
      Math.abs(Math.log(step / ideal)) < Math.abs(Math.log(best / ideal)) ? step : best
    );
  }

  function ticks(min, max, step) {
    const values = [];
    for (let i = Math.ceil(min / step); i <= Math.floor(max / step); i++) {
      values.push(i * step);
    }
    return values;
  }

  function create(container, flight) {
    const id = `flight-diagram-${++sceneId}`;
    const samples = flight.samples;
    const first = samples[0];
    const last = samples[samples.length - 1];
    const peak = flight.apogee;
    const bounds = samples.reduce((extent, sample) => ({
      left: Math.min(extent.left, sample.x), right: Math.max(extent.right, sample.x),
      high: Math.max(extent.high, sample.z)
    }), { left: 0, right: 0, high: 0 });

    const svg = element(container, 'svg', {
      viewBox: '0 0 720 360', width: '100%', height: '100%', role: 'img',
      'aria-labelledby': `${id}-title ${id}-description`, 'font-family': serif
    });
    svg.style.display = 'block';
    element(svg, 'title', { id: `${id}-title` }, 'Flugbahn in der Seitenansicht');
    element(svg, 'desc', { id: `${id}-description` },
      `Horizontale Position und Höhe in Metern. Der höchste Punkt liegt bei ${number.format(peak.z)} Metern.`);
    const root = element(svg, 'g');
    let grid, travelled, upcoming, marker, projectX, projectZ;
    let width, height, equalScale, points;
    let time = first.t, sample = first, settings = { grid: true, trail: true, equal: true };
    let cachedIndex, prefix, suffix;

    function drawFlight() {
      if (!points) return;
      let lo = 0, hi = points.length;
      while (lo < hi) {
        const mid = Math.floor((lo + hi) / 2);
        if (points[mid].t <= time) lo = mid + 1;
        else hi = mid;
      }
      if (lo !== cachedIndex) {
        cachedIndex = lo;
        prefix = points.slice(0, lo).map(point => point.coord).join(' ');
        suffix = points.slice(lo).map(point => point.coord).join(' ');
      }
      const x = projectX(sample.x), y = projectZ(sample.z);
      const coord = `${x.toFixed(2)},${y.toFixed(2)}`;
      travelled.setAttribute('points', `${prefix} ${coord}`);
      upcoming.setAttribute('points', `${coord} ${suffix}`);
      travelled.style.display = settings.trail ? '' : 'none';
      grid.style.display = settings.grid ? '' : 'none';

      marker.setAttribute('cx', x);
      marker.setAttribute('cy', y);
    }

    function resize() {
      const box = svg.getBoundingClientRect();
      const w = Math.round(box.width), h = Math.round(box.height);
      if (w < 100 || h < 104) return;
      if (w === width && h === height && settings.equal === equalScale) return;
      width = w;
      height = h;
      equalScale = settings.equal;
      svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      root.replaceChildren();
      const small = w < 420;
      let left = small ? 44 : 54, right = w - (small ? 22 : 28);
      let top = 36, ground = h - 48;
      const spanX = Math.max(1, bounds.right - bounds.left);
      let xMin = bounds.left - 0.04 * spanX, xMax = bounds.right + 0.04 * spanX;
      let zMax = Math.max(1, bounds.high) * 1.12;
      if (equalScale) {
        const availableWidth = right - left, availableHeight = ground - top;
        const scale = Math.min(availableWidth / (xMax - xMin), availableHeight / zMax);
        // Letterbox the data range. A small minimum axis length leaves room for tick labels
        // even when the trajectory is almost perfectly vertical or horizontal.
        const plotWidth = Math.max((xMax - xMin) * scale, Math.min(availableWidth, 88));
        const plotHeight = Math.max(zMax * scale, Math.min(availableHeight, 65));
        const xCentre = (xMin + xMax) / 2;
        xMin = xCentre - plotWidth / (2 * scale);
        xMax = xCentre + plotWidth / (2 * scale);
        zMax = plotHeight / scale;
        left += (availableWidth - plotWidth) / 2;
        right = left + plotWidth;
        top += (availableHeight - plotHeight) / 2;
        ground = top + plotHeight;
      }
      projectX = x => left + (x - xMin) * (right - left) / (xMax - xMin);
      projectZ = z => ground - z * (ground - top) / zMax;

      element(root, 'rect', { x: 0, y: 0, width: w, height: h, fill: 'white' });
      grid = element(root, 'g', { 'aria-hidden': 'true' });
      const axes = element(root, 'g', { fill: muted, 'font-size': small ? 11 : 12 });
      const xStep = tickStep(xMax - xMin, (right - left) / 64);
      const zStep = tickStep(zMax, (ground - top) / 54);
      function gridLines(min, max, step, horizontal) {
        const project = horizontal ? projectZ : projectX;
        for (const value of ticks(min, max, step)) {
          const p = project(value);
          const d = horizontal ? `M${left} ${p}H${right}` : `M${p} ${top}V${ground}`;
          element(grid, 'path', { d, fill: 'none', stroke: '#d7d8d2', 'stroke-width': 0.8, 'stroke-dasharray': '2 4' });
          const label = Math.abs(value) >= 100000
            ? value.toExponential(2).replace(/\.?0+e/, 'e').replace('e+', 'e').replace('.', ',')
            : number.format(value || 0);
          if (horizontal) {
            element(axes, 'path', { d: `M${left - 4} ${p}h4`, stroke: ink });
            element(axes, 'text', { x: left - 8, y: p + 4, 'text-anchor': 'end' }, label);
          } else {
            element(axes, 'path', { d: `M${p} ${ground}v4`, stroke: ink });
            element(axes, 'text', { x: p, y: ground + 18, 'text-anchor': 'middle' }, label);
          }
        }
      }
      gridLines(xMin, xMax, xStep, false);
      gridLines(0, zMax, zStep, true);
      element(axes, 'path', { d: `M${left} ${top}V${ground}H${right}`, fill: 'none', stroke: ink, 'stroke-width': 1 });
      function axisLabel(symbol, x, y, anchor) {
        const label = element(axes, 'text', { x, y, 'text-anchor': anchor, fill: ink, 'font-size': 14 });
        element(label, 'tspan', { 'font-style': 'italic' }, symbol);
        element(label, 'tspan', {}, ' / m');
      }
      axisLabel('z', left, top - 12, 'start');
      axisLabel('x', (left + right) / 2, ground + 39, 'middle');

      // Thin densely sampled runs to about one point per screen pixel during playback.
      points = [];
      let prevX, prevY;
      for (const s of samples) {
        const x = projectX(s.x), y = projectZ(s.z);
        if (points.length && s !== last && Math.hypot(x - prevX, y - prevY) < 1.1) continue;
        points.push({ t: s.t, coord: `${x.toFixed(2)},${y.toFixed(2)}` });
        prevX = x;
        prevY = y;
      }
      cachedIndex = -1;
      upcoming = element(root, 'polyline', { fill: 'none', stroke: '#575953', 'stroke-width': 1.5, 'stroke-dasharray': '5 4', 'stroke-linejoin': 'round' });
      travelled = element(root, 'polyline', { fill: 'none', stroke: ink, 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });

      for (const end of [first, last]) {
        element(root, 'circle', { cx: projectX(end.x), cy: projectZ(end.z), r: 2.7, fill: 'white', stroke: ink, 'stroke-width': 1.1 });
      }
      const peakX = projectX(peak.x), peakY = projectZ(peak.z);
      const heightLabel = `${number.format(peak.z)} m`;
      const leader = element(root, 'path', { fill: 'none', stroke: '#85877e', 'stroke-width': 0.8 });
      const label = element(root, 'text', { fill: muted, 'font-size': 12 });
      let lines = [element(label, 'tspan', {}, `Scheitelpunkt · ${heightLabel}`)];
      const textWidth = node => node.getComputedTextLength?.() || node.textContent.length * 6.3;
      const labelLeft = left + 6, labelRight = right - 5;
      if (textWidth(lines[0]) > labelRight - labelLeft) {
        lines[0].textContent = 'Scheitelpunkt';
        lines.push(element(label, 'tspan', {}, heightLabel));
      }
      const labelWidth = Math.max(...lines.map(textWidth));
      let labelX = peakX - labelWidth / 2;
      if (peakX + 14 + labelWidth <= labelRight) labelX = peakX + 14;
      else if (peakX - 14 - labelWidth >= labelLeft) labelX = peakX - 14 - labelWidth;
      labelX = Math.max(labelLeft, Math.min(labelX, labelRight - labelWidth));
      const labelBottom = Math.max(16 + (lines.length - 1) * 14, peakY - 15);
      lines.forEach((line, index) => {
        line.setAttribute('x', labelX);
        line.setAttribute('y', labelBottom - (lines.length - 1 - index) * 14);
      });
      const leaderX = Math.max(labelX, Math.min(peakX, labelX + labelWidth));
      leader.setAttribute('d', `M${peakX} ${peakY - 3}L${leaderX} ${labelBottom + 3}`);
      element(root, 'circle', { cx: peakX, cy: peakY, r: 2.7, fill: 'white', stroke: ink, 'stroke-width': 1.1 });

      marker = element(root, 'circle', { r: 4.8, fill: current, stroke: 'white', 'stroke-width': 1.4, 'aria-hidden': 'true' });
      drawFlight();
    }

    function update(nextTime, nextSample, nextSettings) {
      time = nextTime;
      sample = nextSample;
      settings = { grid: nextSettings?.grid ?? true, trail: nextSettings?.trail ?? true, equal: nextSettings?.equal ?? true };
      if (settings.equal !== equalScale) resize();
      else drawFlight();
    }

    resize();
    const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
    if (observer) observer.observe(container);
    else window.addEventListener('resize', resize);
    return { update, resize, destroy() {
      if (observer) observer.disconnect();
      else window.removeEventListener('resize', resize);
      svg.remove();
    } };
  }

  window.FlightScene = { create };
})();
