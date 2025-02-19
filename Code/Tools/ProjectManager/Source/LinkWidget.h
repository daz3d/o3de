/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 */

#pragma once

#if !defined(Q_MOC_RUN)
#include <QLabel>
#include <QUrl>
#endif

QT_FORWARD_DECLARE_CLASS(QEvent)
QT_FORWARD_DECLARE_CLASS(QMouseEvent)
QT_FORWARD_DECLARE_CLASS(QWidget)

namespace O3DE::ProjectManager
{
    class LinkLabel
        : public QLabel
    {
        Q_OBJECT // AUTOMOC

    public:
        LinkLabel(const QString& text = {}, const QUrl& url = {}, QWidget* parent = nullptr);

        void SetUrl(const QUrl& url);

    signals:
        void clicked();

    private:
        void mousePressEvent(QMouseEvent* event) override;
        void enterEvent(QEvent* event) override;
        void leaveEvent(QEvent* event) override;
        void SetDefaultStyle();

    private:
        QUrl m_url;
    };
} // namespace O3DE::ProjectManager
