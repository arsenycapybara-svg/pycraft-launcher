import QtQuick
import "../theme"

Item {
    id: root
    property string skinUrl: ""
    property string maskUrl: ""
    property bool slim: false
    property real yaw: 0.6
    property real pitch: 0.18
    property real velocity: 0
    property bool dragging: false
    property bool touched: false
    readonly property int tex: 16     // масштаб текстуры (как SCALE в skins.py)

    property bool ready: false
    property string curSkin: ""
    property string curMask: ""

    function sync() {
        if (!ready) return
        if (curSkin !== skinUrl) {
            if (curSkin !== "") canvas.unloadImage(curSkin)
            curSkin = skinUrl
            if (curSkin !== "") canvas.loadImage(curSkin)
        }
        if (curMask !== maskUrl) {
            if (curMask !== "") canvas.unloadImage(curMask)
            curMask = maskUrl
            if (curMask !== "") canvas.loadImage(curMask)
        }
        canvas.requestPaint()
    }

    Component.onCompleted: { ready = true; sync() }
    onSkinUrlChanged: sync()
    onMaskUrlChanged: sync()
    onSlimChanged: canvas.requestPaint()
    onYawChanged: canvas.requestPaint()
    onPitchChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    function draw(ctx, W, H) {
        ctx.clearRect(0, 0, W, H)

        var unit = Math.min(W / 20, H / 38)
        var cx0 = W / 2
        var cy0 = H * 0.46
        var cyw = Math.cos(yaw)
        var syw = Math.sin(yaw)
        var cp = Math.cos(pitch)
        var sp = Math.sin(pitch)
        var ac = Theme.accent

        function rot(x, y, z) {
            var x1 = x * cyw + z * syw
            var z1 = -x * syw + z * cyw
            return [x1, y * cp - z1 * sp, y * sp + z1 * cp]
        }
        function col(a) { return Qt.rgba(ac.r, ac.g, ac.b, a) }

        // свечение за персонажем
        var glow = ctx.createRadialGradient(cx0, cy0, 0, cx0, cy0, unit * 22)
        glow.addColorStop(0, col(0.26))
        glow.addColorStop(1, col(0))
        ctx.fillStyle = glow
        ctx.fillRect(0, 0, W, H)

        // голографическая площадка
        var gy = cy0 + 16 * cp * unit
        var ry = Math.max(sp, 0.08)
        function ringPath(r) {
            ctx.beginPath()
            for (var i = 0; i <= 72; i++) {
                var t = i / 72 * Math.PI * 2
                var px = cx0 + Math.cos(t) * r * unit
                var py = gy + Math.sin(t) * r * unit * ry
                if (i === 0) ctx.moveTo(px, py)
                else ctx.lineTo(px, py)
            }
        }
        ringPath(15)
        ctx.fillStyle = col(0.07)
        ctx.fill()
        ctx.lineWidth = 1.5
        ctx.strokeStyle = col(0.75)
        ringPath(15)
        ctx.stroke()
        ctx.strokeStyle = col(0.3)
        ringPath(19)
        ctx.stroke()
        ctx.strokeStyle = col(0.6)
        ctx.beginPath()
        for (var k = 0; k < 24; k++) {
            var a = k * Math.PI / 12 + yaw
            ctx.moveTo(cx0 + Math.cos(a) * 19 * unit, gy + Math.sin(a) * 19 * unit * ry)
            ctx.lineTo(cx0 + Math.cos(a) * 20.6 * unit, gy + Math.sin(a) * 20.6 * unit * ry)
        }
        ctx.stroke()

        if (curSkin === "" || curMask === ""
                || !canvas.isImageLoaded(curSkin) || !canvas.isImageLoaded(curMask)) return

        // части тела: u, v, ширина, высота, глубина, x, y, z, раздутие слоя
        var aw = slim ? 3 : 4
        var armX = 4 + aw / 2
        var parts = [
            [0, 0, 8, 8, 8, 0, 28, 0, 0],
            [16, 16, 8, 12, 4, 0, 18, 0, 0],
            [40, 16, aw, 12, 4, -armX, 18, 0, 0],
            [32, 48, aw, 12, 4, armX, 18, 0, 0],
            [0, 16, 4, 12, 4, -2, 6, 0, 0],
            [16, 48, 4, 12, 4, 2, 6, 0, 0],
            [32, 0, 8, 8, 8, 0, 28, 0, 0.5],
            [16, 32, 8, 12, 4, 0, 18, 0, 0.25],
            [40, 32, aw, 12, 4, -armX, 18, 0, 0.25],
            [48, 48, aw, 12, 4, armX, 18, 0, 0.25],
            [0, 32, 4, 12, 4, -2, 6, 0, 0.25],
            [0, 48, 4, 12, 4, 2, 6, 0, 0.25]
        ]

        var faces = []
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i]
            var u = p[0], v = p[1], w = p[2], h = p[3], d = p[4]
            var cx = p[5], cy = p[6] - 16, cz = p[7], g = p[8]
            var hx = w / 2 + g, hy = h / 2 + g, hz = d / 2 + g

            // текстура (x, y, w, h), начало O, оси U и V, нормаль N
            var defs = [
                [u + d, v + d, w, h, [cx - hx, cy + hy, cz + hz], [2 * hx, 0, 0], [0, -2 * hy, 0], [0, 0, 1]],
                [u + 2 * d + w, v + d, w, h, [cx + hx, cy + hy, cz - hz], [-2 * hx, 0, 0], [0, -2 * hy, 0], [0, 0, -1]],
                [u, v + d, d, h, [cx - hx, cy + hy, cz - hz], [0, 0, 2 * hz], [0, -2 * hy, 0], [-1, 0, 0]],
                [u + d + w, v + d, d, h, [cx + hx, cy + hy, cz + hz], [0, 0, -2 * hz], [0, -2 * hy, 0], [1, 0, 0]],
                [u + d, v, w, d, [cx - hx, cy + hy, cz - hz], [2 * hx, 0, 0], [0, 0, 2 * hz], [0, 1, 0]]
            ]
            for (var j = 0; j < defs.length; j++) {
                var f = defs[j]
                var n = rot(f[7][0], f[7][1], f[7][2])
                if (n[2] <= 0.0001) continue           // грань смотрит от камеры
                var o = rot(f[4][0], f[4][1], f[4][2])
                var uu = rot(f[5][0], f[5][1], f[5][2])
                var vv = rot(f[6][0], f[6][1], f[6][2])
                var lit = Math.max(0, -0.35 * n[0] + 0.55 * n[1] + 0.76 * n[2])
                faces.push({
                    z: o[2] + (uu[2] + vv[2]) / 2,
                    sx: f[0] * tex, sy: f[1] * tex, sw: f[2] * tex, sh: f[3] * tex,
                    ox: cx0 + o[0] * unit, oy: cy0 - o[1] * unit,
                    ax: uu[0] * unit, ay: -uu[1] * unit,
                    bx: vv[0] * unit, by: -vv[1] * unit,
                    dark: 0.5 * (1 - lit)
                })
            }
        }
        faces.sort(function (a, b) { return a.z - b.z })

        for (var m = 0; m < faces.length; m++) {
            var q = faces[m]
            ctx.save()
            ctx.transform(q.ax / q.sw, q.ay / q.sw, q.bx / q.sh, q.by / q.sh, q.ox, q.oy)
            ctx.drawImage(curSkin, q.sx, q.sy, q.sw, q.sh, -0.35, -0.35, q.sw + 0.7, q.sh + 0.7)
            if (q.dark > 0.02) {
                ctx.globalAlpha = q.dark
                ctx.drawImage(curMask, q.sx, q.sy, q.sw, q.sh, -0.35, -0.35, q.sw + 0.7, q.sh + 0.7)
                ctx.globalAlpha = 1
            }
            ctx.restore()
        }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        onImageLoaded: requestPaint()
        onPaint: root.draw(getContext("2d"), width, height)
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        cursorShape: root.dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        property real lastX: 0
        property real lastY: 0

        onPressed: function (m) {
            root.dragging = true
            root.touched = true
            root.velocity = 0
            lastX = m.x
            lastY = m.y
        }
        onPositionChanged: function (m) {
            if (!pressed) return
            var dx = m.x - lastX
            var dy = m.y - lastY
            lastX = m.x
            lastY = m.y
            root.yaw += dx * 0.012
            root.velocity = dx * 0.012
            root.pitch = Math.max(0.02, Math.min(0.85, root.pitch + dy * 0.006))
        }
        onReleased: root.dragging = false
        onCanceled: root.dragging = false
    }

    // инерция после броска и медленное вращение, когда курсор не над моделью
    Timer {
        interval: 16
        repeat: true
        running: root.visible && root.width > 0
        onTriggered: {
            if (root.dragging) return
            if (Math.abs(root.velocity) > 0.0004) {
                root.yaw += root.velocity
                root.velocity *= 0.94
            } else {
                root.velocity = 0
                if (!ma.containsMouse) root.yaw += 0.007
            }
        }
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 8
        text: "Зажмите ЛКМ и вращайте"
        color: Theme.textFaint
        font.pixelSize: 11
        opacity: root.touched ? 0 : 0.8
        Behavior on opacity { NumberAnimation { duration: 400 } }
    }
}