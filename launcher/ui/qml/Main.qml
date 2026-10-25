import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "theme"
import "components"
import "pages"

ApplicationWindow {
    id: win
    width: 1280
    height: 800
    minimumWidth: 980
    minimumHeight: 640
    visibility: Window.Maximized
    flags: Qt.Window | Qt.FramelessWindowHint
    color: Theme.bg
    title: "PyCraft Launcher"

    Binding { target: Theme; property: "accent"; value: backend.accent }

    property int current: 0            // 0..4 — пункты меню, 5 — аккаунты
    property string accountsTab: "offline"
    readonly property int navStep: 58
    readonly property var navItems: [
        { icon: "play",     name: "Главная" },
        { icon: "folder",   name: "Профили" },
        { icon: "versions", name: "Версии" },
        { icon: "mods",     name: "Моды" },
        { icon: "settings", name: "Настройки" }
    ]

    function go(i) {
        if (i === current) return
        current = i
        stack.replace([homeComp, profilesComp, versionsComp, modsComp, settingsComp, accountsComp][i])
    }

    function openAccounts(tab) {
        accountsTab = tab
        go(5)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TitleBar { Layout.fillWidth: true; Layout.preferredHeight: 38; win: win }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ----- боковая панель -----
            Item {
                Layout.preferredWidth: 276
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 34
                    anchors.rightMargin: 22
                    anchors.topMargin: 26
                    anchors.bottomMargin: 22
                    spacing: 0

                    Text {
                        text: "МЕНЮ"
                        color: Theme.textFaint
                        font.pixelSize: 11
                        font.letterSpacing: 1.6
                        font.weight: Font.DemiBold
                        bottomPadding: 16
                        leftPadding: 6
                    }

                    Item {
                        id: navCol
                        Layout.fillWidth: true
                        Layout.preferredHeight: win.navItems.length * win.navStep

                        Rectangle {
                            x: -34
                            width: 3
                            height: 24
                            radius: 2
                            color: Theme.accent
                            y: (win.current < 5 ? win.current : 0) * win.navStep + 12
                            opacity: win.current < 5 ? 1 : 0
                            Behavior on y { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }
                            Behavior on opacity { NumberAnimation { duration: Theme.animFast } }
                        }

                        Repeater {
                            model: win.navItems
                            SidebarItem {
                                y: index * win.navStep
                                width: navCol.width
                                height: 48
                                text: modelData.name
                                icon: modelData.icon
                                active: win.current === index
                                onClicked: win.go(index)
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    // профиль аккаунта
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 66
                        radius: Theme.radius
                        color: win.current === 5 ? Theme.accentSoft
                             : pMouse.containsMouse ? Theme.surfaceHover : Theme.surface
                        border.width: 1
                        border.color: win.current === 5 ? Theme.accent : Theme.border
                        Behavior on color { ColorAnimation { duration: Theme.animFast } }

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12

                            Avatar {
                                Layout.preferredWidth: 40
                                Layout.preferredHeight: 40
                                name: backend.selectedName
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Text {
                                    Layout.fillWidth: true
                                    text: backend.selectedName !== "" ? backend.selectedName : "Нет аккаунта"
                                    color: Theme.text
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Text {
                                    text: backend.selectedName === "" ? "Нажмите, чтобы добавить"
                                        : Theme.typeName(backend.selectedType)
                                    color: Theme.textDim
                                    font.pixelSize: 12
                                }
                            }
                        }

                        MouseArea {
                            id: pMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: win.openAccounts(backend.selectedType !== "" ? backend.selectedType : "offline")
                        }
                    }
                }
            }

            // ----- контент -----
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rightMargin: 14
                Layout.bottomMargin: 14
                radius: Theme.radiusLg
                color: Theme.surface
                border.width: 1
                border.color: Theme.border
                clip: true

                StackView {
                    id: stack
                    anchors.fill: parent
                    initialItem: homeComp

                    replaceEnter: Transition {
                        ParallelAnimation {
                            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.animNormal }
                            NumberAnimation { property: "y"; from: 18; to: 0; duration: Theme.animNormal; easing.type: Easing.OutCubic }
                        }
                    }
                    replaceExit: Transition {
                        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.animFast }
                    }
                }
            }
        }
    }

    // тонкая рамка окна (когда не развёрнуто)
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.width: 1
        border.color: Theme.border
        visible: win.visibility !== Window.Maximized
        enabled: false
        z: 150
    }

    // края для изменения размера безрамочного окна
    ResizeEdge { z: 200; edges: Qt.LeftEdge;   cursorShape: Qt.SizeHorCursor; width: 5; anchors { left: parent.left;  top: parent.top;    bottom: parent.bottom; topMargin: 8; bottomMargin: 8 } }
    ResizeEdge { z: 200; edges: Qt.RightEdge;  cursorShape: Qt.SizeHorCursor; width: 5; anchors { right: parent.right; top: parent.top;    bottom: parent.bottom; topMargin: 8; bottomMargin: 8 } }
    ResizeEdge { z: 200; edges: Qt.TopEdge;    cursorShape: Qt.SizeVerCursor; height: 5; anchors { top: parent.top;    left: parent.left;  right: parent.right;  leftMargin: 8; rightMargin: 100 } }
    ResizeEdge { z: 200; edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor; height: 5; anchors { bottom: parent.bottom; left: parent.left; right: parent.right;  leftMargin: 8; rightMargin: 8 } }
    ResizeEdge { z: 200; edges: Qt.TopEdge | Qt.LeftEdge;     cursorShape: Qt.SizeFDiagCursor; width: 8; height: 8; anchors { left: parent.left;   top: parent.top } }
    ResizeEdge { z: 200; edges: Qt.BottomEdge | Qt.LeftEdge;  cursorShape: Qt.SizeBDiagCursor; width: 8; height: 8; anchors { left: parent.left;   bottom: parent.bottom } }
    ResizeEdge { z: 200; edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor; width: 8; height: 8; anchors { right: parent.right; bottom: parent.bottom } }

    Component { id: homeComp;     HomePage {} }
    Component { id: profilesComp; ProfilesPage {} }
    Component { id: versionsComp; VersionsPage {} }
    Component { id: modsComp;     ModsPage {} }
    Component { id: settingsComp; SettingsPage {} }
    Component { id: accountsComp; AccountsPage {} }
}