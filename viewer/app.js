(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const digits = [1, 2].map(places => new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: places, maximumFractionDigits: places, signDisplay: 'negative'
  }));
  const decimal = value => digits[0].format(value);
  const precision = value => digits[1].format(value);

  function readFlight(data) {
    if (!data || !Array.isArray(data.samples) || data.samples.length < 2) {
      throw new Error('Flugdaten fehlen.');
    }
    let previous = -Infinity;
    const samples = data.samples.map(row => {
      if (!Array.isArray(row) || row.length !== 6 || !row.every(Number.isFinite) || row[0] <= previous) {
        throw new Error('Die Messreihe ist ungültig.');
      }
      const [t, x, z, vx, vz, m] = row;
      previous = t;
      return { t, x, z, vx, vz, m };
    });
    if (samples[0].t !== 0 || !Number.isFinite(data.burnout) || !Number.isFinite(data.dt) || data.dt <= 0) {
      throw new Error('Die Zeitangaben sind ungültig.');
    }
    const last = samples[samples.length - 1];
    const apogee = samples.reduce((peak, sample) => sample.z > peak.z ? sample : peak);
    return { samples, duration: last.t, burnout: data.burnout, dt: data.dt, apogee, landed: last.z === 0 && last.vz < 0 };
  }

  function sampleAt(samples, t) {
    let lo = 0, hi = samples.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >>> 1;
      if (samples[mid].t <= t) lo = mid;
      else hi = mid;
    }
    const a = samples[lo], b = samples[hi];
    if (t === a.t) return a;
    if (t === b.t) return b;
    const f = (t - a.t) / (b.t - a.t);
    const mix = (first, second) => first + f * (second - first);
    return { t, x: mix(a.x, b.x), z: mix(a.z, b.z), vx: mix(a.vx, b.vx), vz: mix(a.vz, b.vz), m: mix(a.m, b.m) };
  }

  function start(flight) {
    const { samples, duration, burnout, apogee } = flight;
    const scene = window.FlightScene.create(byId('scene'), flight);
    const telemetry = window.FlightTelemetry.create(byId('telemetry'), flight, seek);
    const timeline = byId('timeline');
    const settings = { grid: true, trail: true, equal: true };
    let metric = 'all';
    let time = 0, frame = 0, previousStamp = 0, playing = false;
    timeline.max = String(duration);
    byId('duration').textContent = precision(duration);
    byId('model-step').textContent = new Intl.NumberFormat('de-DE', {maximumFractionDigits: 4}).format(flight.dt * 1000);

    const events = [{ t: 0, name: 'Start' }];
    if (burnout > 0 && burnout < duration) events.push({ t: burnout, name: 'Brennschluss' });
    if (apogee.t > 0 && apogee.t < duration) events.push({ t: apogee.t, name: 'Scheitelpunkt' });
    events.push({ t: duration, name: flight.landed ? 'Bodenkontakt' : 'Simulationsende' });
    events.sort((a, b) => a.t - b.t);
    for (const event of events) {
      const button = document.createElement('button');
      button.className = 'event';
      button.title = 'Zu ' + event.name + ' springen';
      const label = document.createElement('span');
      label.className = 'event-name';
      label.textContent = event.name;
      const stamp = document.createElement('time');
      stamp.dateTime = 'PT' + event.t + 'S';
      stamp.textContent = precision(event.t) + ' s';
      button.append(label, stamp);
      button.addEventListener('click', () => seek(event.t));
      byId('event-list').appendChild(button);
      event.button = button;
    }

    function show() {
      const sample = sampleAt(samples, time);
      const phase = time === 0 ? 'Start' : time === duration ? events[events.length - 1].name :
        time === apogee.t ? 'Scheitelpunkt' : sample.vz < 0 && time > apogee.t ? 'Sinkflug' :
        time < burnout ? 'Antrieb' : 'Steigflug';
      const phaseLabel = byId('phase');
      if (phaseLabel.textContent !== phase) phaseLabel.textContent = phase;
      timeline.value = String(time);
      timeline.style.setProperty('--progress', (100 * time / duration) + '%');
      timeline.setAttribute('aria-valuetext', precision(time) + ' Sekunden');
      byId('time').textContent = precision(time);
      byId('table-time').textContent = precision(time);
      byId('altitude').textContent = decimal(sample.z);
      byId('speed').textContent = decimal(Math.hypot(sample.vx, sample.vz));
      byId('distance').textContent = decimal(sample.x);
      byId('mass').textContent = precision(sample.m);
      byId('play-text').textContent = playing ? 'Pause' : time === duration ? 'Wiederholen' : 'Abspielen';
      byId('play-icon').setAttribute('href', playing ? '#i-pause' : '#i-play');
      events.forEach((event, index) => {
        const reached = time >= event.t;
        event.button.dataset.reached = String(reached);
        event.button.setAttribute('aria-current', String(reached && (!events[index + 1] || time < events[index + 1].t)));
      });
      scene.update(time, sample, settings);
      telemetry.update(time, sample, metric);
    }

    function pause() {
      playing = false;
      cancelAnimationFrame(frame);
    }

    function seek(value) {
      pause();
      time = Math.min(duration, Math.max(0, value));
      show();
    }

    function advance(stamp) {
      time = Math.min(duration, time + (stamp - previousStamp) * Number(byId('rate').value) / 1000);
      previousStamp = stamp;
      if (time === duration) playing = false;
      show();
      if (playing) frame = requestAnimationFrame(advance);
    }

    function toggle() {
      if (playing) {
        pause();
      } else {
        if (time >= duration) time = 0;
        playing = true;
        previousStamp = performance.now();
        frame = requestAnimationFrame(advance);
      }
      show();
    }

    byId('play').addEventListener('click', toggle);
    byId('reset').addEventListener('click', () => seek(0));
    timeline.addEventListener('input', () => seek(Number(timeline.value)));
    document.addEventListener('visibilitychange', () => {
      if (document.hidden && playing) { pause(); show(); }
    });
    document.addEventListener('keydown', event => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.target !== document.body && event.target !== timeline) return;
      if (event.code === 'Space') {
        event.preventDefault();
        if (!event.repeat) toggle();
        return;
      }
      const step = event.shiftKey ? 1 : 0.25;
      const targets = { ArrowLeft: time - step, ArrowRight: time + step, Home: 0, End: duration };
      if (Object.hasOwn(targets, event.key)) {
        event.preventDefault();
        seek(targets[event.key]);
      }
    });
    for (const key of Object.keys(settings)) {
      const button = byId(key + '-toggle');
      button.addEventListener('click', () => {
        settings[key] = !settings[key];
        button.setAttribute('aria-pressed', String(settings[key]));
        show();
      });
    }
    byId('metric').addEventListener('change', event => {
      metric = event.target.value;
      show();
    });
    show();
  }

  try {
    start(readFlight(window.FLIGHT_DATA));
  } catch (error) {
    console.error(error);
    const notice = byId('load-error');
    notice.hidden = false;
    notice.textContent = 'Die Flugansicht konnte nicht geladen werden. Öffne die Seite erneut oder erzeuge die Flugdaten mit python 2d_sim/main.py --export.';
    document.querySelectorAll('main button, main input, main select').forEach(control => { control.disabled = true; });
  }
})();
