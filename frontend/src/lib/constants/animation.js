export const DEBOUNCETIMEOUT = 150;
export const detailClosedShiftThreshold = 0.2;
export const detailOpenShiftThreshold = 0.05;
export const detailOpenWidthRatio =
    parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue(
            '--detail-open-width'
        )
    ) / 100;
export const rowAnimationIntervalInMs = 30;
export const rowAnimationPickupThreshold = 0.01;
