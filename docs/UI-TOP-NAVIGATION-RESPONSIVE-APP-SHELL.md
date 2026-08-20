# Responsive Top Navigation and App Shell

## Desktop

- The permanent left sidebar has been removed.
- Primary navigation is displayed across the dark top header.
- A second contextual navigation row displays the submenu for the current part of NOP.
- Telecom products are grouped under a compact menu for LNP, DigiCloud, and NTI Mobile.
- Communications and notification alerts remain visible beside the user menu.
- Account, security, user administration, and sign-out actions are available from the user menu.

## Tablet

- At widths below 1180 pixels, primary navigation labels collapse to recognizable icons.
- The contextual submenu remains horizontally scrollable.
- Content uses the full screen width rather than reserving space for a sidebar.

## Phone

- A compact fixed header contains the NTInet logo, message alert, notification alert, and a large red menu button.
- A fixed bottom dock provides one-touch access to Home, Customers, Tickets, Jobs, and the full Menu.
- The Menu button opens an app-style slide-out navigation drawer.
- The drawer is grouped into Main, Field Service, Telecom Services, and Account & Platform sections.
- The drawer closes from its close button, backdrop, Escape key, or after choosing a destination.
- Safe-area padding supports modern phones with bottom gesture areas.

All menu items continue to honor the existing user permissions and organization module assignments.

## Verification

1. Open NOP on a desktop wider than 1180 pixels and confirm labels appear in the primary header.
2. Resize between 901 and 1180 pixels and confirm primary items become icons.
3. Resize to 900 pixels or narrower and confirm the bottom app dock and red menu button appear.
4. Open and close the mobile drawer with the menu button, backdrop, close icon, and Escape key.
5. Sign in with a restricted user and confirm unauthorized modules remain hidden.
