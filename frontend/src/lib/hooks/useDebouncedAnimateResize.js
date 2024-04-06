import React from "react";
import * as Constants from "../constants";
import debounce from "lodash/debounce";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import useResizeObserver from '@react-hook/resize-observer';


export const useDebouncedAnimateResize = (elementRef, elementIdRef) => {
    const {setAnimationState} = useAnimationUpdater();
    const setAnimationStateRef = React.useRef(setAnimationState);
    const animateResize = React.useCallback(
        (key, entry) => {
            const setAnimationState = setAnimationStateRef.current;
            setAnimationState((oldValue) => ({
                ...oldValue,
                [key]: entry.contentRect,
            }));
    }, []);

    const debouncedAnimateResize = React.useMemo(
        () => debounce((key, entry) => animateResize(key, entry), Constants.DEBOUNCETIMEOUT),
        [animateResize]
    );

    React.useEffect(() => {
        const setAnimationState = setAnimationStateRef.current;
        const elementId = elementIdRef.current;
        setAnimationState((oldValue) => ({
            ...oldValue,
            [elementId]: null,
        }));
        return () => {
            setAnimationState((v) => {
                const {[elementId]: _, ...rest} = v;
                return rest;
            });
        };
    }, [elementIdRef]);

    useResizeObserver(elementRef, (entry) =>
        debouncedAnimateResize(elementIdRef.current, entry)
    );


};