import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../theme"
import "../components"

Item {
    id: page
    readonly property var host: Window.window
    readonly property string tab: host ? host.accountsTab : "offline"
    property string error: ""
    property bool linkOpened: false

    function count(kind) {
        var n = 0
        var l = backend.accounts
        for (var i = 0; i < l.length; i++)
            if (l[i].type === kind) n++
        return n
    }

    Connections {
        target: backend
        function onErrorOccurred(msg) { page.error = msg }
        function onAccountsChanged() { page.error = "" }
        function onMsChanged() {
            if (backend.msCode !== "" && !page.linkOpened) {
                page.linkOpened = true
                backend.openMicrosoftLink()
            }
            if (backend.msCode === "") page.linkOpened = false
        }
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        padding: 28
        contentWidth: availableWidth

        ColumnLayout {
            width: scroll.availableWidth
            spacing: 16

            Text {
                text: "Аккаунты"
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.Bold
            }

            // ----- переключатель типа -----
            RowLayout {
                spacing: 8

                Repeater {
                    model: ["microsoft", "elyby", "offline"]
                    Chip {
                        text: Theme.typeName(modelData) + "  ·  " + page.count(modelData)
                        active: page.tab === modelData
                        onClicked: if (page.host) page.host.accountsTab = modelData
                    }
                }
            }

            Text {
                visible: page.count(page.tab) === 0
                text: "Аккаунтов этого типа пока нет."
                color: Theme.textDim
                font.pixelSize: 14
            }

            Repeater {
                model: backend.accounts
                delegate: Card {
                    visible: modelData.type === page.tab
                    Layout.fillWidth: true
                    padding: 14
                    borderColor: modelData.selected ? Theme.accent : Theme.border
                    color: modelData.selected ? Theme.surfaceHover : Theme.raised

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        Avatar {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            name: modelData.username
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                text: modelData.username
                                color: Theme.text
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }
                            Text {
                                text: Theme.typeName(modelData.type)
                                color: Theme.textDim
                                font.pixelSize: 13
                            }
                        }

                        Btn {
                            visible: !modelData.selected
                            variant: "secondary"
                            text: "Выбрать"
                            onClicked: backend.selectAccount(index)
                        }
                        Text {
                            visible: modelData.selected
                            text: "✓ Активный"
                            color: Theme.success
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                        Btn {
                            variant: "danger"
                            text: "Удалить"
                            onClicked: backend.removeAccount(index)
                        }
                    }
                }
            }

            // ===== Лицензия (Microsoft) =====
            Card {
                visible: page.tab === "microsoft"
                Layout.fillWidth: true
                padding: 24
                spacing: 12

                Text {
                    text: "Вход через Microsoft"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Лаунчер покажет код. Введите его на странице Microsoft, которая откроется сама, "
                        + "и подтвердите вход. Пароль в лаунчер не вводится."
                    color: Theme.textDim
                    font.pixelSize: 13
                }

                RowLayout {
                    spacing: 10

                    Btn {
                        text: backend.msBusy ? "Ожидание входа..." : "Войти через Microsoft"
                        enabled: !backend.msBusy && backend.msClientId !== ""
                        onClicked: { page.error = ""; backend.startMicrosoft() }
                    }
                    Btn {
                        visible: backend.msBusy
                        variant: "secondary"
                        text: "Отмена"
                        onClicked: backend.cancelMicrosoft()
                    }
                }

                ColumnLayout {
                    visible: backend.msCode !== ""
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "ВАШ КОД"
                        color: Theme.textDim
                        font.pixelSize: 11
                        font.letterSpacing: 1.4
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: backend.msCode
                        color: Theme.accent
                        font.pixelSize: 34
                        font.weight: Font.Bold
                        font.family: "monospace"
                        font.letterSpacing: 4
                    }
                    RowLayout {
                        spacing: 10
                        Btn {
                            variant: "secondary"
                            text: "Открыть страницу"
                            onClicked: backend.openMicrosoftLink()
                        }
                        Btn {
                            variant: "secondary"
                            text: "Скопировать код"
                            onClicked: backend.copyToClipboard(backend.msCode)
                        }
                    }
                }

                Text {
                    visible: backend.msStatus !== ""
                    text: backend.msStatus
                    color: Theme.textDim
                    font.pixelSize: 13
                }
            }

            Card {
                visible: page.tab === "microsoft"
                Layout.fillWidth: true
                padding: 24
                spacing: 12

                Text {
                    text: "Приложение Azure (Client ID)"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Theme.textDim
                    font.pixelSize: 13
                    text: "1. Azure Portal → Microsoft Entra ID → App registrations → New registration.\n"
                        + "2. Тип учётных записей: «Personal Microsoft accounts only» (или «…and personal»).\n"
                        + "3. В разделе Authentication включите «Allow public client flows».\n"
                        + "4. Скопируйте «Application (client) ID» и вставьте ниже.\n"
                        + "5. Насколько мне известно, Mojang пускает к Minecraft API только одобренные приложения "
                        + "(форма aka.ms/AppRegInfo). Пока одобрения нет, вход завершится ошибкой «Invalid app registration»."
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Field {
                        id: msClient
                        Layout.fillWidth: true
                        placeholderText: "Application (client) ID"
                        Component.onCompleted: text = backend.msClientId
                        onAccepted: backend.setMsClientId(text)
                    }
                    Btn {
                        text: "Сохранить"
                        onClicked: backend.setMsClientId(msClient.text)
                    }
                }
                RowLayout {
                    spacing: 10
                    Btn {
                        variant: "secondary"
                        text: "Открыть Azure Portal"
                        onClicked: Qt.openUrlExternally("https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade")
                    }
                    Btn {
                        variant: "secondary"
                        text: "Требования Mojang"
                        onClicked: Qt.openUrlExternally("https://aka.ms/AppRegInfo")
                    }
                }
            }

            // ===== Ely.by =====
            Card {
                visible: page.tab === "elyby"
                Layout.fillWidth: true
                padding: 24
                spacing: 12

                Text {
                    text: "Вход через Ely.by"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Field { id: login; Layout.fillWidth: true; placeholderText: "Логин или e-mail" }
                Field { id: pass; Layout.fillWidth: true; placeholderText: "Пароль"; echoMode: TextInput.Password }
                Field { id: totp; Layout.fillWidth: true; placeholderText: "Код 2FA (если включён)" }

                RowLayout {
                    spacing: 10
                    Btn {
                        text: backend.busy ? "Вход..." : "Войти через Ely.by"
                        enabled: !backend.busy
                        onClicked: { backend.addElyby(login.text, pass.text, totp.text); pass.clear() }
                    }
                    Btn {
                        variant: "secondary"
                        text: "Зарегистрироваться"
                        onClicked: backend.openElybyRegister()
                    }
                }
            }

            // ===== Пиратский (оффлайн) =====
            Card {
                visible: page.tab === "offline"
                Layout.fillWidth: true
                padding: 24
                spacing: 12

                Text {
                    text: "Пиратский аккаунт"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Достаточно ника, без проверки лицензии. В игре будет стандартный скин, "
                        + "а на серверах с проверкой лицензии такой аккаунт не пустят."
                    color: Theme.textDim
                    font.pixelSize: 13
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Field {
                        id: nick
                        Layout.fillWidth: true
                        placeholderText: "Ник (3–16 символов)"
                        onAccepted: addBtn.clicked()
                    }
                    Btn {
                        id: addBtn
                        text: "Добавить"
                        onClicked: { backend.addOffline(nick.text); nick.clear() }
                    }
                }
            }

            ErrorBox { message: page.error }

            Item { Layout.preferredHeight: 8 }
        }
    }
}