import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "../theme"

Card {
    id: root
    readonly property var host: Window.window
    property string error: ""
    property string info: ""
    property bool confirmReset: false

    padding: 18
    spacing: 12

    Connections {
        target: skin
        function onErrorOccurred(msg) { root.error = msg; root.info = "" }
        function onInfoMessage(msg) { root.info = msg; root.error = "" }
    }
    Connections {
        target: backend
        function onAccountsChanged() { root.error = ""; root.info = ""; root.confirmReset = false }
    }

    Timer { id: resetTimer; interval: 4000; onTriggered: root.confirmReset = false }

    function doReset() {
        if (backend.selectedType === "microsoft" && !confirmReset) {
            confirmReset = true
            resetTimer.restart()
            return
        }
        confirmReset = false
        skin.resetSkin()
    }

    FileDialog {
        id: fileDlg
        title: "Файл скина (PNG)"
        nameFilters: ["PNG (*.png)"]
        onAccepted: { root.error = ""; skin.uploadFile(selectedFile.toString()) }
    }

    // ----- тип аккаунта прямо в профиле -----
    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        Repeater {
            model: ["microsoft", "elyby", "offline"]
            Chip {
                text: Theme.typeName(modelData)
                active: backend.selectedType === modelData
                onClicked: {
                    if (!backend.selectType(modelData) && root.host)
                        root.host.openAccounts(modelData)
                }
            }
        }
    }

    Text {
        Layout.fillWidth: true
        text: backend.selectedName !== "" ? backend.selectedName : "Гость"
        color: Theme.text
        font.pixelSize: 22
        font.weight: Font.Bold
        elide: Text.ElideRight
    }

    // ----- 3D-вьювер -----
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 200
        radius: Theme.radius
        color: "#0d0d10"
        border.width: 1
        border.color: Theme.border
        clip: true

        SkinViewer {
            anchors.fill: parent
            skinUrl: skin.viewUrl
            maskUrl: skin.maskUrl
            slim: skin.slim
        }

        // бегущая линия сканера
        Rectangle {
            id: scan
            width: parent.width
            height: 1
            color: Theme.accent
            opacity: 0.22
            SequentialAnimation on y {
                loops: Animation.Infinite
                running: root.visible
                NumberAnimation { from: 0; to: scan.parent.height; duration: 3600; easing.type: Easing.InOutSine }
                NumberAnimation { from: scan.parent.height; to: 0; duration: 3600; easing.type: Easing.InOutSine }
            }
        }

        // уголки в углах
        Repeater {
            model: 4
            Item {
                width: 16
                height: 16
                x: (index % 2 === 0) ? 8 : parent.width - 24
                y: (index < 2) ? 8 : parent.height - 24
                Rectangle { width: 16; height: 2; y: index < 2 ? 0 : 14; color: Theme.accent; opacity: 0.8 }
                Rectangle { width: 2; height: 16; x: index % 2 === 0 ? 0 : 14; color: Theme.accent; opacity: 0.8 }
            }
        }

        BusyIndicator {
            anchors.centerIn: parent
            running: skin.busy
            visible: skin.busy
        }
    }

    Text {
        Layout.fillWidth: true
        text: skin.note
        color: Theme.textFaint
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    Text {
        visible: root.info !== ""
        Layout.fillWidth: true
        text: root.info
        color: Theme.success
        font.pixelSize: 13
        wrapMode: Text.WordWrap
    }

    ErrorBox { message: root.error }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Btn {
            Layout.fillWidth: true
            variant: "secondary"
            text: "Изменить скин"
            enabled: !skin.busy && backend.selectedName !== ""
            onClicked: pop.open()
        }
        Btn {
            Layout.fillWidth: true
            variant: root.confirmReset ? "danger" : "secondary"
            text: root.confirmReset ? "Точно сбросить?" : "Сбросить"
            enabled: !skin.busy && backend.selectedName !== ""
            onClicked: root.doReset()
        }
    }

    Popup {
        id: pop
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 400
        padding: 22
        onAboutToShow: nickField.text = backend.selectedName

        Overlay.modal: Rectangle { color: "#99000000" }
        enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 150 } }
        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.raised
            border.width: 1
            border.color: Theme.border
        }

        contentItem: ColumnLayout {
            spacing: 12

            Text {
                text: "Изменить скин"
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.Bold
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Theme.textDim
                font.pixelSize: 13
                text: backend.selectedType === "microsoft"
                    ? "Файл будет загружен в ваш профиль Minecraft: скин изменится и в игре, и на серверах."
                    : backend.selectedType === "elyby"
                    ? "В игре скин Ely.by меняется на сайте ely.by. Здесь можно выбрать скин для просмотра в лаунчере."
                    : "Пиратский режим: скин виден только в лаунчере, в игре останется стандартный."
            }

            Btn {
                Layout.fillWidth: true
                text: "Загрузить .png..."
                icon: "folder"
                onClicked: { pop.close(); fileDlg.open() }
            }
            Btn {
                visible: backend.selectedType === "elyby"
                Layout.fillWidth: true
                variant: "secondary"
                text: "Открыть сайт Ely.by"
                onClicked: Qt.openUrlExternally("https://ely.by/skins")
            }

            Text {
                text: backend.selectedType === "microsoft" ? "Обновить из профиля" : "Взять скин по нику"
                color: Theme.textDim
                font.pixelSize: 13
                topPadding: 4
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Field {
                    id: nickField
                    Layout.fillWidth: true
                    visible: backend.selectedType !== "microsoft"
                    placeholderText: "Ник игрока"
                    onAccepted: { skin.fetchByNick(text); pop.close() }
                }
                Btn {
                    Layout.fillWidth: backend.selectedType === "microsoft"
                    variant: "secondary"
                    text: "Обновить"
                    onClicked: { skin.fetchByNick(nickField.text); pop.close() }
                }
            }

            Btn {
                Layout.fillWidth: true
                variant: "ghost"
                text: "Закрыть"
                onClicked: pop.close()
            }
        }
    }
}