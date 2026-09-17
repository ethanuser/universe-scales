// Run in a browser console on the locally served site, or with agent-browser eval.
(async () => {
    const results = [];
    const check = (name, ok) => {
        results.push({ name, ok: Boolean(ok) });
        if (!ok) throw new Error(name);
    };
    const tick = () =>
        new Promise((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(resolve))
        );
    const dimensions = [
        'length',
        'area',
        'volume',
        'counts',
        'speed',
        'acceleration',
        'jerk',
        'frequency',
        'sound-frequency',
        'angular-velocity',
        'brightness',
        'angle',
        'visual-angle'
    ];
    for (const dimension of dimensions) {
        localStorage.removeItem(`scale-view:${dimension}`);
        await app.setDimension(dimension);
        const view = app.experiences;
        await tick();
        check(
            `${dimension}: defaults to interactive`,
            view.active && !view.host.hidden && app.plotContainer.hidden
        );
        check(
            `${dimension}: item selected`,
            Boolean(view.detail.querySelector('h2')?.textContent)
        );
        for (const index of [
            0,
            Math.floor(view.items.length / 2),
            view.items.length - 1
        ]) {
            view.focus(index);
            await tick();
            check(
                `${dimension}: finite geometry at item ${index}`,
                !/="[^"]*(?:NaN|Infinity)/.test(view.stage.innerHTML)
            );
        }
        view.logButton.click();
        await tick();
        check(
            `${dimension}: log switch`,
            !view.active &&
                !app.plotContainer.hidden &&
                app.svg.attr('width') > 0
        );
        view.interactiveButton.click();
        await tick();
        check(
            `${dimension}: switch back`,
            view.active && view.host.querySelector('.experience-stage')
        );
    }
    const view = app.experiences;
    await app.setDimension('length');
    view.logButton.click();
    await app.setDimension('mass');
    check(
        'unsupported dimension: original plot',
        !view.active && view.switcher.hidden
    );
    await app.setDimension('length');
    check('mode remembered independently', !view.active);
    await app.setDimension('area');
    check('area still interactive', view.active);
    view.focus(view.items.findIndex((i) => i.name === 'Earth surface area'));
    await new Promise((resolve) => setTimeout(resolve, 500));
    check(
        'equal-area Earth map',
        view.stage.querySelectorAll('path').length >= 2
    );
    await app.setDimension('counts');
    view.focus(view.items.length - 1);
    check(
        'Go positions: distinct rendered boards',
        view.stage.querySelectorAll('circle').length > 30
    );
    await app.setDimension('speed');
    view.playButton.click();
    await new Promise((resolve) => setTimeout(resolve, 200));
    check('motion time advances', view.clock.time > 0);
    await app.setDimension('mass');
    check('animation stops on dimension change', !view.clock.playing);
    await app.setDimension('angle');
    view.logButton.click();
    app.showTooltip(
        { clientX: 300, clientY: 300 },
        app.getAllItems().find((i) => i.name === 'Right angle'),
        true
    );
    check(
        'angle tooltip has diagram',
        app.tooltip.querySelector('.angle-diagram')
    );
    app.hideTooltip();
    await app.setDimension('sound-intensity');
    check('loudness stays on plot', !view.active);
    const rain = app.getAllItems().find((i) => i.name === 'Rainfall');
    app.showTooltip({ clientX: 300, clientY: 300 }, rain, true);
    await view.audio.ready;
    check(
        'sound has click-to-play',
        app.tooltip.querySelector('.experience-audio button')
    );
    check(
        'rain recording registered',
        view.audio.clips.Rainfall.src.endsWith('rain.ogg')
    );
    app.hideTooltip();
    check('audio stops with tooltip', !view.audio.player && !view.audio.node);
    await app.setDimension('length');
    view.setMode('interactive');
    check(
        'no page horizontal overflow',
        document.documentElement.scrollWidth <= innerWidth + 1
    );
    return { passed: results.length, results };
})();
