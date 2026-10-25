import QtQuick
import QtQuick.Layouts
import "../theme"

Card {
    padding: 24
    spacing: 12

    Text {
        text: "Источник загрузок"
        color: Theme.text
        font.pixelSize: 16
        font.weight: Font.DemiBold
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "«Авто»: сначала официальные серверы, при сбое зеркало BMCLAPI. «Зеркало»: сначала BMCLAPI. "
            + "Обрывы скачивания лаунчер сам докачивает с того же места."
        color: Theme.textDim
        font.pixelSize: 13
    }

    RowLayout {
        spacing: 8

        Chip {
            text: "Зеркало (BMCLAPI)"
            active: cfg.downloadSource === "mirror"
            onClicked: cfg.setDownloadSource("mirror")
        }
        Chip {
            text: "Авто"
            active: cfg.downloadSource === "auto"
            onClicked: cfg.setDownloadSource("auto")
        }
        Chip {
            text: "Официальные серверы"
            active: cfg.downloadSource === "official"
            onClicked: cfg.setDownloadSource("official")
        }
    }

    Text {
        text: "Свой Forge-мирор (необязательно)"
        color: Theme.textDim
        font.pixelSize: 13
        topPadding: 6
    }
    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Адрес до папки maven, например https://example.com/maven. Пробуется раньше BMCLAPI."
        color: Theme.textFaint
        font.pixelSize: 12
    }
    Field {
        id: forgeField
        Layout.fillWidth: true
        placeholderText: "https://..."
        Component.onCompleted: text = backend.forgeMirror
        onEditingFinished: backend.setForgeMirror(text)
    }
}