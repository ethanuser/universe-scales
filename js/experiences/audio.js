(function (root) {
    const { dom, button, Slider } = ScaleControls;
    const attenuationLabel = (db) => db === 0 ? 'Full preview' : `${Math.abs(db)} dB quieter`;
    class ScaleAudio {
        constructor(app) {
            this.app = app;
            this.generation = 0;
            this.trim = -12;
            this.referenceDb = null;
            this.referencePlayed = false;
            this.cache = new Map();
            this.clips = {};
            this.ready = fetch('content/visualizations/assets.json', { cache: 'no-cache' })
                .then((r) => r.ok ? r.json() : {})
                .then((data) => { this.clips = data.audio || {}; })
                .catch(() => { this.clips = {}; });
        }
        stop(message) {
            this.generation++;
            clearTimeout(this.timer);
            this.timer = null;
            cancelAnimationFrame(this.frame);
            this.frame = null;
            this.abort?.abort();
            this.abort = null;
            this.playbackCleanup?.();
            this.playbackCleanup = null;
            if (this.node) {
                this.node.onended = null;
                try { this.node.stop(); } catch {}
            }
            for (const key of ['node', 'gain', 'attenuation', 'analyser']) {
                this[key]?.disconnect();
                this[key] = null;
            }
            if (this.currentButton) {
                this.currentButton.textContent = this.currentButton.dataset.label || 'Play sound';
                this.currentButton.setAttribute('aria-pressed', 'false');
                this.currentButton.removeAttribute('aria-busy');
            }
            if (this.active) {
                this.active.status.textContent = message || (this.active.reference
                    ? 'Reference stopped. Play it to the end before applying a measurement.' : 'Playback stopped.');
                this.resetMeter(this.active.view);
            }
            this.currentButton = null;
            this.active = null;
            if (!this.referencePlayed && this.referenceDb == null) this.unwatchOutput();
            this.syncCalibration();
        }
        muteMusic() {
            this.app.backgroundMusic?.pause();
            if (this.app.enableAudioHandler) {
                for (const type of ['click', 'keydown', 'touchstart'])
                    document.removeEventListener(type, this.app.enableAudioHandler);
                this.app.enableAudioHandler = null;
            }
            this.app.musicToggle?.classList.remove('playing');
            if (this.app.musicToggle) this.app.musicToggle.textContent = '\uD83C\uDFB5';
        }
        contextForPlayback() {
            this.context ||= new (window.AudioContext || window.webkitAudioContext)();
            return this.context;
        }
        controls(parent, item) {
            this.stop();
            const wrapper = dom('section', 'experience-audio');
            const header = dom('div', 'audio-heading');
            header.append(dom('h3', '', 'Recorded sound'));
            const badge = dom('span', 'audio-calibration-badge');
            const reset = button(header, 'Reset', () => {
                this.resetCalibration();
                status.textContent = 'Measurement reset. Using relative previews.';
            });
            reset.classList.add('audio-reset');
            reset.setAttribute('aria-label', 'Reset calibration');
            header.insertBefore(badge, reset);
            // Keep Play as the first button for existing controller integrations.
            wrapper.append(dom('p', 'experience-note audio-quiet', 'Start with low device volume. Previews begin quietly.'));
            const transport = dom('div', 'audio-transport');
            const status = dom('p', 'experience-note audio-status', 'Loading recording details...');
            status.setAttribute('role', 'status');
            status.setAttribute('aria-live', 'polite');
            status.setAttribute('aria-atomic', 'true');
            const play = button(transport, 'Play sound', () => {
                if (this.currentButton === play) return this.stop();
                this.play(item, play, status);
            });
            play.classList.add('audio-play');
            play.dataset.label = 'Play sound';
            play.setAttribute('aria-pressed', 'false');
            play.disabled = true;
            const meterBox = dom('div', 'audio-meter');
            const meterLabel = dom('div', 'audio-meter__label');
            const meterText = dom('span', '', 'Idle');
            meterLabel.append(dom('span', '', 'Digital level'), meterText);
            const meter = dom('meter');
            Object.assign(meter, { min: -96, max: 0, low: -18, high: -6, optimum: -48, value: -96 });
            meter.setAttribute('aria-label', 'Digital preview level, not room sound level');
            const meterScale = dom('div', 'audio-meter__scale');
            meterScale.append(dom('span', '', '-96'), dom('span', '', 'dBFS'), dom('span', '', '0'));
            meterBox.append(meterLabel, meter, meterScale);
            transport.append(meterBox);
            wrapper.append(transport, header);
            const options = dom('details', 'audio-options');
            options.append(dom('summary', '', 'Playback options & source'));
            const clearLabel = dom('label', 'audio-mode');
            const clear = dom('input');
            clear.type = 'checkbox';
            clearLabel.append(clear, document.createTextNode(' Hear recording clearly'));
            const modeHint = dom('p', 'experience-note audio-mode-hint', 'Relative mode follows the scale; quiet examples may be barely audible.');
            clear.addEventListener('change', () => {
                this.stop();
                modeHint.textContent = clear.checked
                    ? 'Clear mode uses a consistent preview level, not the plotted loudness.'
                    : 'Relative mode follows the scale; quiet examples may be barely audible.';
                status.textContent = 'Mode changed. Press Play sound to listen.';
            });
            play.clearPreview = clear;
            options.append(clearLabel, modeHint);
            const slider = new Slider(wrapper, {
                label: 'Preview level', min: -40, max: 0, step: 1, value: this.trim,
                format: attenuationLabel,
                onChange: (x) => {
                    this.trim = x;
                    slider.input.setAttribute('aria-valuetext', attenuationLabel(x));
                    if (this.attenuation && !this.active.reference) {
                        const now = this.context.currentTime;
                        this.attenuation.gain.cancelScheduledValues(now);
                        this.attenuation.gain.setTargetAtTime(ScaleAudioMath.attenuationGain(x), now, 0.02);
                        this.describePlayback();
                    } else if (!this.active) status.textContent = `${attenuationLabel(x)}. Applied on your next preview.`;
                }
            });
            slider.input.setAttribute('aria-valuetext', attenuationLabel(this.trim));
            const ends = dom('div', 'audio-slider-ends');
            ends.append(dom('span', '', 'Quieter'), dom('span', '', 'Full preview'));
            wrapper.append(ends, status);

            const details = dom('details', 'audio-calibration');
            details.append(dom('summary', '', 'Optional measured reference'));
            const steps = dom('ol', 'experience-note');
            for (const text of [
                'Keep device volume low. Play the entire fixed-level rain reference; the Preview level slider does not change it.',
                'Use an external SPL meter at your listening position. Measure across the full reference, then enter your reading.',
                'Keep output device, system volume and listening position unchanged. Reset and remeasure after any change.'
            ]) steps.append(dom('li', '', text));
            details.append(steps);
            const reference = button(details, 'Play rain reference', () => {
                if (this.currentButton === reference) return this.stop();
                this.play({ name: 'Rainfall' }, reference, status, true);
            });
            reference.dataset.label = 'Play rain reference';
            reference.setAttribute('aria-pressed', 'false');
            reference.disabled = true;
            const label = dom('label', 'audio-measurement', 'Your measured reference (dB SPL)');
            const input = dom('input');
            Object.assign(input, { type: 'number', min: '20', max: '85', step: '0.1', value: this.referenceDb ?? '' });
            input.inputMode = 'decimal';
            label.append(input);
            details.append(label);
            const apply = button(details, 'Apply measurement', () => {
                const n = input.valueAsNumber;
                if (!this.referencePlayed || this.active?.reference || !Number.isFinite(n) || n < 20 || n > 85) {
                    status.textContent = 'Finish the rain reference, then enter a measured reading between 20 and 85 dB SPL.';
                    input.setAttribute('aria-invalid', 'true');
                    return;
                }
                this.stop();
                this.referenceDb = n;
                input.removeAttribute('aria-invalid');
                this.syncCalibration();
                status.textContent = 'Measured reference applied for this session only. Speaker output is not verified.';
            });
            details.append(dom('p', 'experience-note', 'One reference adjusts relative gain; it cannot calibrate every recording, frequency or speaker. No actual output SPL is measured by this page.'));
            if (navigator.mediaDevices?.selectAudioOutput && (window.AudioContext || window.webkitAudioContext)?.prototype.setSinkId) {
                const choose = button(details, 'Choose output device', async () => {
                    this.resetCalibration();
                    const generation = this.generation;
                    this.selectingOutput = true;
                    choose.disabled = true;
                    status.textContent = 'Choose an output, then measure a new reference.';
                    try {
                        const device = await navigator.mediaDevices.selectAudioOutput();
                        if (generation !== this.generation || !wrapper.isConnected) return;
                        await this.contextForPlayback().setSinkId(device.deviceId);
                        if (generation === this.generation) status.textContent = `Output: ${device.label || 'selected device'}. Measure a new reference.`;
                    } catch {
                        if (generation === this.generation) status.textContent = 'Output selection unavailable or cancelled. Use system sound settings; measure again afterward.';
                    } finally {
                        this.selectingOutput = false;
                        choose.disabled = false;
                    }
                });
            }
            const info = dom('details', 'audio-info');
            info.append(dom('summary', '', 'About these previews & recording source'));
            info.append(dom('p', 'experience-note',
                'Real recordings are normalized and capped for comparison, not a reproduction of the real event. Recording distance and equipment differ from the plotted examples. The meter shows the digital preview signal (dBFS), not acoustic dB SPL.'));
            info.append(dom('p', 'experience-note',
                'The browser cannot read OS volume or measure your speakers. Device-change detection is limited and may miss a route change; it cannot detect changes in volume or listening position. Never raise device volume to chase an inaudible scale example; try clear mode instead.'));
            const attribution = dom('p', 'experience-note audio-attribution');
            info.append(attribution);
            options.append(details, info);
            wrapper.append(options);
            parent.append(wrapper);
            const view = { wrapper, play, reference, badge, reset, input, apply, meter, meterText, status };
            play.audioView = reference.audioView = view;
            this.view = view;
            this.resetMeter(view);
            this.syncCalibration();
            this.ready.then(() => {
                if (!wrapper.isConnected) return;
                const clip = this.clips[item.name];
                const supported = !!(window.AudioContext || window.webkitAudioContext);
                play.disabled = !clip || !supported;
                reference.disabled = !this.clips.Rainfall || !supported;
                if (clip) this.credit(attribution, clip);
                if (this.currentButton || this.view !== view) return;
                status.textContent = !supported ? 'Audio playback is unavailable in this browser.'
                    : clip ? 'Ready. Real recording, quiet preview.'
                        : 'No verified recording for this item yet. No synthesized substitute is played.';
            });
        }
        syncCalibration() {
            const view = this.view;
            if (!view) return;
            const applied = this.referenceDb != null;
            view.badge.textContent = applied ? 'Measurement applied / this session'
                : this.referencePlayed ? 'Reference ready' : 'Relative preview';
            view.badge.title = applied ? 'Session only. Actual speaker output is not verified.'
                : this.referencePlayed ? 'Enter your external meter reading under Playback options.' : 'Not physically calibrated.';
            view.badge.dataset.applied = String(applied);
            view.reset.hidden = !applied && !this.referencePlayed;
            view.apply.disabled = !this.referencePlayed || !!this.active?.reference;
            view.input.disabled = !this.referencePlayed || !!this.active?.reference;
        }
        resetCalibration() {
            this.referenceDb = null;
            this.referencePlayed = false;
            this.stop();
            this.unwatchOutput();
            if (this.view) {
                this.view.input.value = '';
                this.view.input.removeAttribute('aria-invalid');
            }
            this.syncCalibration();
        }
        watchOutput() {
            if (this.outputChanged) return;
            this.outputChanged = () => {
                this.resetCalibration();
                if (this.view) this.view.status.textContent = 'Audio devices changed. Measurement reset; play and measure the reference again.';
            };
            navigator.mediaDevices?.addEventListener('devicechange', this.outputChanged);
            this.context?.addEventListener('sinkchange', this.outputChanged);
        }
        unwatchOutput() {
            if (!this.outputChanged) return;
            navigator.mediaDevices?.removeEventListener('devicechange', this.outputChanged);
            this.context?.removeEventListener('sinkchange', this.outputChanged);
            this.outputChanged = null;
        }
        resetMeter(view) {
            if (!view) return;
            view.meter.value = -96;
            view.meter.setAttribute('aria-valuetext', 'Idle');
            view.meterText.textContent = 'Idle';
            view.wrapper.dataset.playing = 'false';
        }
        startMeter(generation) {
            const view = this.active.view;
            if (!view) return;
            const samples = new Float32Array(this.analyser.fftSize);
            let last = -Infinity;
            view.wrapper.dataset.playing = 'true';
            const tick = (time) => {
                if (generation !== this.generation) return;
                if (!view.wrapper.isConnected) return this.stop();
                if (time - last >= 100) {
                    last = time;
                    this.analyser.getFloatTimeDomainData(samples);
                    const db = ScaleAudioMath.digitalLevel(samples);
                    view.meter.value = db;
                    const text = db <= -96 ? 'Below -96 dBFS' : `${db.toFixed(1)} dBFS`;
                    view.meterText.textContent = text;
                    view.meter.setAttribute('aria-valuetext', text);
                }
                this.frame = requestAnimationFrame(tick);
            };
            this.frame = requestAnimationFrame(tick);
        }
        credit(element, clip) {
            element.replaceChildren(document.createTextNode(`${clip.title}. ${clip.author}; ${clip.license}. `));
            const link = dom('a', '', 'Recording source');
            link.href = clip.source; link.target = '_blank'; link.rel = 'noopener noreferrer';
            element.append(link);
            if (clip.license_url) {
                const license = dom('a', '', 'License');
                license.href = clip.license_url;
                license.target = '_blank'; license.rel = 'noopener noreferrer';
                element.append(document.createTextNode(' / '), license);
            }
            if (clip.changes) element.append(document.createTextNode(` ${clip.changes}.`));
        }
        async recording(clip, signal) {
            const key = `${clip.src}:${clip.start || 0}`;
            if (this.cache.has(key)) return this.cache.get(key);
            const response = await fetch(clip.src, { signal });
            if (!response.ok) throw new Error('Recording download failed');
            const bytes = await response.arrayBuffer();
            if (bytes.byteLength > 20000000) throw new Error('Recording too large');
            const decoded = await this.context.decodeAudioData(bytes);
            if (signal.aborted) throw new Error('Playback cancelled');
            const start = Math.floor((clip.start || 0) * decoded.sampleRate);
            const length = Math.min(decoded.length - start, Math.floor(decoded.sampleRate * 6));
            if (!Number.isFinite(start) || start < 0 || length <= 0) throw new Error('Invalid recording excerpt');
            const buffer = this.context.createBuffer(decoded.numberOfChannels, length, decoded.sampleRate);
            let energy = 0, peak = 0;
            for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
                const data = decoded.getChannelData(channel).subarray(start, start + length);
                buffer.copyToChannel(data, channel);
                for (const x of data) { energy += x * x; peak = Math.max(peak, Math.abs(x)); }
            }
            const result = { buffer, rms: Math.sqrt(energy / (length * buffer.numberOfChannels)), peak };
            if (!(result.rms > 1e-7) || !Number.isFinite(result.rms) || !Number.isFinite(peak)) throw new Error('Invalid recording');
            this.cache.set(key, result);
            return result;
        }
        describePlayback() {
            const { reference, status, baseLevel, clear } = this.active;
            status.textContent = reference ? 'Playing fixed-level rain reference. Measure the entire excerpt; wait for it to finish.'
                : `${clear ? 'Clear recording' : 'Scale-relative preview'}: ${(baseLevel.relativeDb + this.trim).toFixed(1)} dB relative to the fixed reference. ${attenuationLabel(this.trim)}.${baseLevel.limited ? ' Preview capped; event loudness is not reproduced.' : ''}`;
        }
        async play(item, play, status, reference = false) {
            if (this.selectingOutput) {
                status.textContent = 'Finish choosing an output before playing.';
                return;
            }
            this.stop();
            if (reference) this.resetCalibration();
            this.muteMusic();
            const generation = this.generation;
            this.currentButton = play;
            play.textContent = 'Cancel loading';
            play.setAttribute('aria-pressed', 'true');
            play.setAttribute('aria-busy', 'true');
            this.active = { reference, status, view: play.audioView, clear: !!play.clearPreview?.checked };
            status.textContent = 'Loading real recording...';
            this.abort = new AbortController();
            const signal = this.abort.signal;
            this.timer = setTimeout(() => {
                if (generation === this.generation) this.stop('Recording timed out. Press Play sound to try again.');
            }, 15000);
            const onHidden = () => { if (document.hidden) this.stop(); };
            const onPageHide = () => this.stop();
            document.addEventListener('visibilitychange', onHidden);
            window.addEventListener('pagehide', onPageHide);
            this.playbackCleanup = () => {
                document.removeEventListener('visibilitychange', onHidden);
                window.removeEventListener('pagehide', onPageHide);
            };
            try {
                // Resume in the click handler before any network wait.
                await this.contextForPlayback().resume();
                if (generation !== this.generation) return;
                await this.ready;
                if (generation !== this.generation) return;
                const clip = this.clips[reference ? 'Rainfall' : item.name];
                if (!clip) throw new Error('No recording');
                const recording = await this.recording(clip, signal);
                if (generation !== this.generation) return;
                if (play.audioView && !play.audioView.wrapper.isConnected) return this.stop();
                clearTimeout(this.timer);
                const referenceDb = this.referenceDb ?? 70;
                const targetDb = reference ? 70 : this.active.clear ? referenceDb : ScaleMath.soundLevel(item.value);
                const level = ScaleAudioMath.playbackLevel(recording.rms, recording.peak,
                    targetDb, reference ? 70 : referenceDb, !reference && this.referenceDb != null);
                if (reference && level.limited) throw new Error('Reference crest factor too high');
                this.active.baseLevel = level;
                this.node = this.context.createBufferSource();
                this.node.buffer = recording.buffer;
                this.gain = this.context.createGain();
                this.attenuation = this.context.createGain();
                this.analyser = this.context.createAnalyser();
                this.analyser.fftSize = 1024;
                const now = this.context.currentTime;
                const fade = Math.min(0.03, recording.buffer.duration / 3);
                this.gain.gain.setValueAtTime(0, now);
                this.gain.gain.linearRampToValueAtTime(level.gain, now + fade);
                this.gain.gain.setValueAtTime(level.gain, now + recording.buffer.duration - fade);
                this.gain.gain.linearRampToValueAtTime(0, now + recording.buffer.duration);
                this.attenuation.gain.setValueAtTime(reference ? 1 : ScaleAudioMath.attenuationGain(this.trim), now);
                this.node.connect(this.gain).connect(this.attenuation).connect(this.analyser).connect(this.context.destination);
                this.node.onended = () => {
                    if (generation !== this.generation) return;
                    if (reference) this.referencePlayed = true;
                    this.stop(reference ? 'Reference finished. Enter your measured reading and apply it.' : 'Preview finished.');
                };
                if (reference || this.referenceDb != null) this.watchOutput();
                this.node.start();
                play.textContent = reference ? 'Stop reference' : 'Stop sound';
                play.removeAttribute('aria-busy');
                this.describePlayback();
                this.syncCalibration();
                this.startMeter(generation);
                this.timer = setTimeout(() => {
                    if (generation === this.generation) this.stop('Playback stopped.');
                }, recording.buffer.duration * 1000 + 500);
            } catch {
                if (generation !== this.generation) return;
                this.stop('Recording could not be played. No synthesized substitute is used.');
            }
        }
    }
    root.ScaleAudio = ScaleAudio;
})(globalThis);
