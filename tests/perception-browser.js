// Run on the locally served app in a fresh session, at desktop and mobile widths.
(async () => {
    const results = [];
    const check = (name, ok) => {
        results.push({ name, ok: Boolean(ok) });
        if (!ok) throw new Error(name);
    };
    const tick = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const view = app.experiences;
    const geometry = () => {
        const bounds = view.stage.viewBox.baseVal;
        for (const element of view.stage.querySelectorAll('*')) {
            for (const attribute of element.attributes) {
                if (['aria-label', 'href'].includes(attribute.name)) continue;
                check(`finite ${element.tagName}.${attribute.name}`, !/NaN|Infinity/.test(attribute.value));
            }
        }
        for (const image of view.stage.querySelectorAll('image')) {
            const x = Number(image.getAttribute('x')), y = Number(image.getAttribute('y'));
            const w = Number(image.getAttribute('width')), h = Number(image.getAttribute('height'));
            check('photo within viewBox', x >= -0.1 && y >= 0 && x + w <= bounds.width + 0.1 && y + h <= bounds.height);
            check('photo aspect ratio preserved', image.getAttribute('preserveAspectRatio') === 'xMidYMid meet');
        }
        check('finite positive stage bounds', bounds.width > 0 && bounds.height > 0 && Number.isFinite(bounds.width + bounds.height));
        check('stage matches viewBox aspect ratio', Math.abs(view.stage.getBoundingClientRect().width / view.stage.getBoundingClientRect().height - bounds.width / bounds.height) < 0.02);
    };
    for (const dimension of ['brightness', 'angle', 'visual-angle']) {
        localStorage.removeItem(`scale-view:${dimension}`);
        await app.setDimension(dimension);
        await tick();
        check(`${dimension}: correct active attribute`, document.body.dataset.experienceDimension === dimension);
        const info = view.caption.closest('details');
        check(`${dimension}: Info closed by default`, info && !info.open);
        check(`${dimension}: calibration closed by default`, !view.settings.querySelector('details').open);
        check(`${dimension}: caption not visible by default`, !view.caption.checkVisibility());
        check(`${dimension}: no prose notes among controls`, !view.settings.querySelector('.experience-note'));
        check(`${dimension}: item slider available`, view.settings.querySelector('input[type="range"]'));
        for (let index = 0; index < view.items.length; index++) {
            view.focus(index);
            await tick();
            geometry();
        }
        view.focus(Math.floor(view.items.length / 2));
        await tick();
        const slider = view.settings.querySelector('input[type="range"]');
        slider.value = 0;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        check(`${dimension}: slider selects item`, view.index === 0);
        view.next.click();
        check(`${dimension}: navigation updates slider`, Number(slider.value) === view.index);
        info.open = true;
        check(`${dimension}: Info reveals explanation`, view.caption.checkVisibility());
        info.open = false;
        check(`${dimension}: no horizontal overflow`, document.documentElement.scrollWidth <= innerWidth + 1);
        if (dimension === 'brightness') {
            check('brightness: black page', getComputedStyle(document.body).backgroundColor === 'rgb(0, 0, 0)');
            check('brightness: gray text', getComputedStyle(document.body).color === 'rgb(189, 189, 189)');
            check('brightness: no opaque light patches', [...view.stage.querySelectorAll('rect')].every((rect) => rect.getAttribute('fill') === 'transparent'));
            check('brightness: relative-only explanation', /relative photo illustration/i.test(view.caption.textContent));
            view.logButton.click();
            check('brightness: dark override removed in log mode', document.body.dataset.experienceDimension !== 'brightness');
        }
    }
    await app.setDimension('brightness');
    view.setMode('interactive');
    view.focus(view.items.findIndex((item) => item.name === 'LED Screen'));
    return { passed: results.length, viewport: innerWidth, results };
})();
