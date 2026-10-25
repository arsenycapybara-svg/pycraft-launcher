import QtQuick
import QtQuick.Layouts
import "../theme"

Card {
    id: root
    padding: 24
    spacing: 14

    readonly property var modes: [
        { id: "none",  name: "Ничего",          hint: "Лаунчер остаётся открытым во время игры." },
        { id: "tray",  name: "Свернуть в трей", hint: "Окно уходит в системный трей и возвращается, когда игра закроется. Иконку в трее можно нажать, чтобы открыть лаунчер раньше." },
        { id: "hide",  name: "Скрыть окно",     hint: "Окно полностью скрывается на время игры и возвращается, когда игра закроется." },
        { id: "close", name: "Закрыть лаунчер", hint: "Лаунчер закрывается после успешного старта. Время игры и статус Discord в этом режиме не сохраняются." }
    ]

    Text {
        text: "При запуске игры"
        color: Theme.text
        font.pixelSize: 16
        font.weight: Font.DemiBold
    }

    RowLayout {
        spacing: 8

        Repeater {
            model: root.modes
            Chip {
                text: modelData.name
                active: behavior.hideMode === modelData.id
                onClicked: behavior.setHideMode(modelData.id)
            }
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: {
            for (var i = 0; i < root.modes.length; i++)
                if (root.modes[i].id === behavior.hideMode) return root.modes[i].hint
            return ""
        }
        color: Theme.textDim
        font.pixelSize: 13
    }

    Text {
        visible: behavior.hideMode === "tray" && !behavior.trayAvailable
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Системный трей в вашей среде недоступен (например, GNOME без расширения AppIndicator). "
            + "Вместо этого окно будет сворачиваться в панель задач."
        color: Theme.warning
        font.pixelSize: 13
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        Layout.topMargin: 6
        color: Theme.border
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Text {
                text: "Статус в Discord"
                color: Theme.text
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Показывает «В меню PyCraft Launcher» или «Играет в Minecraft 1.21.11 (Fabric)» "
                    + "со временем в игре. Работает, пока открыт клиент Discord."
                color: Theme.textDim
                font.pixelSize: 13
            }
        }
        Toggle {
            checked: behavior.discordEnabled
            onToggled: behavior.setDiscordEnabled(checked)
        }
    }
}