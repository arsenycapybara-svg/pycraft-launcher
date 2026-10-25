pragma Singleton
import QtQuick

QtObject {
    property color accent: "#3b82f6"
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, 0.14)
    readonly property color accentHover: Qt.lighter(accent, 1.12)
    readonly property color accentPressed: Qt.darker(accent, 1.15)

    readonly property color bg: "#121214"
    readonly property color surface: "#18181b"
    readonly property color raised: "#1f1f23"
    readonly property color surfaceHover: "#27272c"
    readonly property color border: "#2a2a30"
    readonly property color text: "#f4f4f5"
    readonly property color textDim: "#a1a1aa"
    readonly property color textFaint: "#71717a"
    readonly property color success: "#34d399"
    readonly property color warning: "#fbbf24"
    readonly property color danger: "#f87171"

    readonly property int radius: 12
    readonly property int radiusLg: 16
    readonly property int animFast: 140
    readonly property int animNormal: 260

    function typeName(kind) {
        if (kind === "microsoft") return "Лицензия"
        if (kind === "elyby") return "Ely.by"
        return "Пиратский"
    }
}