(function (root) {
    const dom = (tag, className, text) => {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;
        return element;
    };
    const svg = (tag, attrs = {}, text) => {
        const element = document.createElementNS(
            'http://www.w3.org/2000/svg',
            tag
        );
        for (const [key, value] of Object.entries(attrs))
            element.setAttribute(key, value);
        if (text !== undefined) element.textContent = text;
        return element;
    };
    const number = (value) => {
        if (value === 0) return '0';
        if (Math.abs(value) >= 0.01 && Math.abs(value) < 10000)
            return Number(value.toPrecision(3)).toLocaleString();
        return value.toExponential(2);
    };
    let controlID = 0;
    class Slider {
        constructor(
            parent,
            { label, min, max, value, step = 0.01, format = number, onChange }
        ) {
            this.element = dom('div', 'experience-slider');
            const row = dom('div', 'experience-slider__label');
            this.input = dom('input');
            this.input.type = 'range';
            this.input.id = `experience-slider-${++controlID}`;
            const title = dom('label', '', label);
            title.htmlFor = this.input.id;
            this.output = dom('output');
            this.output.htmlFor = this.input.id;
            row.append(title, this.output);
            this.format = format;
            Object.assign(this.input, { min, max, value, step });
            this.input.addEventListener('input', () => {
                this.set(this.value);
                onChange(this.value);
            });
            this.element.append(row, this.input);
            parent.append(this.element);
            this.set(value);
        }
        get value() {
            return Number(this.input.value);
        }
        set(value) {
            this.input.value = value;
            this.output.textContent = this.format(this.value);
        }
    }
    class Clock {
        constructor(render) {
            this.render = render;
            this.time = 0;
            this.rate = 1;
            this.playing = false;
        }
        start() {
            if (this.playing) return;
            this.playing = true;
            this.last = null;
            const frame = (now) => {
                if (!this.playing) return;
                if (this.last !== null)
                    this.time +=
                        Math.min(0.1, (now - this.last) / 1000) * this.rate;
                this.last = now;
                this.render(this.time);
                this.frame = requestAnimationFrame(frame);
            };
            this.frame = requestAnimationFrame(frame);
        }
        stop() {
            this.playing = false;
            cancelAnimationFrame(this.frame);
            this.last = null;
        }
        reset() {
            this.time = 0;
            this.last = null;
        }
    }
    const button = (parent, text, action) => {
        const node = dom('button', 'experience-button', text);
        node.type = 'button';
        node.addEventListener('click', action);
        parent.append(node);
        return node;
    };
    const field = (parent, label, value, min, max, change) => {
        const wrapper = dom('label', 'experience-field', label);
        const input = dom('input');
        Object.assign(input, { type: 'number', value, min, max, step: 'any' });
        input.addEventListener('change', () => {
            if (!input.value || !input.checkValidity()) {
                input.reportValidity();
                return;
            }
            change(Number(input.value));
        });
        wrapper.append(input);
        parent.append(wrapper);
        return input;
    };
    root.ScaleControls = { dom, svg, number, Slider, Clock, button, field };
})(globalThis);
