/* The scene projects the solver's horizontal position and altitude onto metric axes. */
(() => {
  'use strict';

  const ns = 'http://www.w3.org/2000/svg';
  const ink = '#193d47';
  const accent = '#007d79';
  const muted = '#536e78';
  const mono = 'ui-monospace, SFMono-Regular, Consolas, monospace';
  const number = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 1 });
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
      'aria-labelledby': `${id}-title ${id}-description`, 'font-family': mono
    });
    svg.style.display = 'block';
    element(svg, 'title', { id: `${id}-title` }, 'Flugbahn in der Seitenansicht');
    element(svg, 'desc', { id: `${id}-description` },
      `Horizontale Position und Höhe in Metern. Der höchste Punkt liegt bei ${number.format(peak.z)} Metern.`);
    const defs = element(svg, 'defs');
    const hatch = element(defs, 'pattern', { id: `${id}-ground`, width: 7, height: 7, patternUnits: 'userSpaceOnUse' });
    element(hatch, 'path', { d: 'M-2 2 L2 -2 M0 7 L7 0 M5 9 L9 5', fill: 'none', stroke: '#b1c5c8', 'stroke-width': 0.8 });
    const wash = element(defs, 'linearGradient', { id: `${id}-sky`, x2: 0, y2: 1, gradientUnits: 'objectBoundingBox' });
    element(wash, 'stop', { offset: 0, 'stop-color': '#f1f7f8' });
    element(wash, 'stop', { offset: 1, 'stop-color': '#fbfdfc' });

    const root = element(svg, 'g');
    let grid, travelled, upcoming, marker, projectX, projectZ;
    let width, height, equalScale, points;
    let time = first.t, sample = first, settings = { grid: true, trail: true, equal: false };
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

      // The symbol follows the tangent of the plotted path. Axes can have different scales.
      let dx = sample.vx, dz = sample.vz;
      if (Math.hypot(dx, dz) < 0.2) {
        const next = samples.find(point => point.t > time && point.z > sample.z + 0.25);
        dx = next ? next.x - sample.x : 0;
        dz = next ? next.z - sample.z : 1;
      }
      const heading = Math.atan2(projectZ(dz) - projectZ(0), projectX(dx) - projectX(0)) * 180 / Math.PI;
      marker.setAttribute('transform', `translate(${x} ${y}) rotate(${heading})`);
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
      const left = small ? 40 : 54, right = w - (small ? 14 : 25);
      const top = 30, ground = h - 53;
      const spanX = Math.max(1, bounds.right - bounds.left);
      let xMin = bounds.left - 0.048 * spanX, xMax = bounds.right + 0.05 * spanX;
      let zMax = Math.max(1, bounds.high) * 1.18;
      if (equalScale) {
        const metresPerPixel = Math.max((xMax - xMin) / (right - left), zMax / (ground - top));
        const xCentre = (xMin + xMax) / 2;
        const halfWidth = (right - left) * metresPerPixel / 2;
        xMin = xCentre - halfWidth;
        xMax = xCentre + halfWidth;
        zMax = (ground - top) * metresPerPixel;
      }
      projectX = x => left + (x - xMin) * (right - left) / (xMax - xMin);
      projectZ = z => ground - z * (ground - top) / zMax;

      element(root, 'rect', { x: 0, y: 0, width: w, height: h, fill: `url(#${id}-sky)` });
      grid = element(root, 'g', { 'aria-hidden': 'true' });
      const axes = element(root, 'g', { fill: muted, 'font-size': small ? 10 : 11 });
      const xStep = tickStep(xMax - xMin, (right - left) / (small ? 67 : 94));
      const zStep = tickStep(zMax, (ground - top) / 62);
      function gridLines(min, max, step, horizontal) {
        const project = horizontal ? projectZ : projectX;
        for (const value of ticks(min, max, step / 4)) {
          const p = project(value);
          const major = Math.abs(value / step - Math.round(value / step)) < 1e-7;
          const d = horizontal ? `M${left} ${p}H${right}` : `M${p} ${top}V${ground}`;
          element(grid, 'path', { d, fill: 'none', stroke: major ? '#c9d9dc' : '#e2ebed', 'stroke-width': major ? 0.9 : 0.65 });
          if (!major) continue;
          if (horizontal) {
            element(axes, 'path', { d: `M${left - 4} ${p}h4`, stroke: '#9ab0b5' });
            element(axes, 'text', { x: left - 8, y: p + 3.5, 'text-anchor': 'end' }, number.format(value));
          } else {
            element(axes, 'path', { d: `M${p} ${ground + 8}v4`, stroke: '#9ab0b5' });
            element(axes, 'text', { x: p, y: ground + 24, 'text-anchor': 'middle' }, number.format(value));
          }
        }
      }
      gridLines(xMin, xMax, xStep, false);
      gridLines(0, zMax, zStep, true);
      element(axes, 'path', { d: `M${left} ${top}V${ground}H${right}`, fill: 'none', stroke: '#94aeb3' });
      element(axes, 'rect', { x: left, y: ground + 1, width: right - left, height: 7, fill: `url(#${id}-ground)` });
      const axisLabel = { fill: '#435f68', 'font-size': small ? 9 : 10, 'font-weight': 600, 'letter-spacing': 0.9 };
      element(axes, 'text', { ...axisLabel, x: left, y: 18 }, 'HÖHE z (m)');
      element(axes, 'text', { ...axisLabel, x: right, y: h - 9, 'text-anchor': 'end' }, 'HORIZONTALE POSITION x (m)');

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
      upcoming = element(root, 'polyline', { fill: 'none', stroke: '#408a8b', 'stroke-width': 2, 'stroke-dasharray': '4 5', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
      travelled = element(root, 'polyline', { fill: 'none', stroke: accent, 'stroke-width': 2.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });

      for (const end of [first, last]) {
        element(root, 'circle', { cx: projectX(end.x), cy: projectZ(end.z), r: 3.6, fill: '#f6faf9', stroke: accent, 'stroke-width': 1.6 });
      }
      const peakX = projectX(peak.x), peakY = projectZ(peak.z);
      const direction = peakX + 94 < right ? 1 : -1;
      const labelX = peakX + direction * 20;
      const labelY = Math.max(22, peakY - 22);
      const anchor = direction === 1 ? 'start' : 'end';
      element(root, 'path', { d: `M${peakX} ${peakY - 4}v-4L${labelX - direction * 5} ${labelY + 3}`, fill: 'none', stroke: '#729295', 'stroke-width': 1 });
      element(root, 'text', { x: labelX, y: labelY, 'text-anchor': anchor, fill: muted, 'font-size': 9, 'letter-spacing': 0.7 }, 'SCHEITELPUNKT');
      element(root, 'text', { x: labelX, y: labelY + 14, 'text-anchor': anchor, fill: ink, 'font-size': 12, 'font-weight': 600 }, `${number.format(peak.z)} m`);
      element(root, 'circle', { cx: peakX, cy: peakY, r: 3.7, fill: 'white', stroke: accent, 'stroke-width': 1.6 });

      marker = element(root, 'g', { 'aria-hidden': 'true' });
      element(marker, 'circle', { r: 15, fill: '#d6efed', 'fill-opacity': 0.65, stroke: accent, 'stroke-opacity': 0.22, 'stroke-width': 1 });
      element(marker, 'path', { d: 'M13 0Q8 -4 0 -3L-3 -3L-8 -7L-7 -2L-10 -1L-10 1L-7 2L-8 7L-3 3L0 3Q8 4 13 0Z', fill: ink, stroke: '#f8fffd', 'stroke-width': 1.1, 'stroke-linejoin': 'round' });
      element(marker, 'circle', { cx: 4.5, cy: 0, r: 1.45, fill: '#a0e1da' });
      drawFlight();
    }

    function update(nextTime, nextSample, nextSettings) {
      time = nextTime;
      sample = nextSample;
      settings = { grid: nextSettings?.grid ?? true, trail: nextSettings?.trail ?? true, equal: nextSettings?.equal ?? false };
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
