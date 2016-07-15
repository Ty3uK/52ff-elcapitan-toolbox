DefinitionBlock ("", "SSDT", 1, "hack", "UIAC", 0)
{
    Device(UIAC)
    {
        Name(_HID, "UIA00000")

        // override XHC configuration to have only one port
        Name(RMCF, Package()
        {
            "EH01", Package()
            {
                "port-count", Buffer() { 1, 0, 0, 0 },
                "ports", Package()
                {
                    "PR11", Package()
                    {
                        "UsbConnector", 0,
                        "port", Buffer() { 1, 0, 0, 0 },
                    }
                }
            },
            "8086_9xxx", Package()
            {
                "port-count", Buffer() { 0xa, 0, 0, 0 },
                "ports", Package()
                {
                    "HS01", Package()
                    {
                        "UsbConnector", 0,
                        "port", Buffer() { 1, 0, 0, 0 },
                    },
                    "HS02", Package()
                    {
                        "UsbConnector", 0,
                        "port", Buffer() { 2, 0, 0, 0 },
                    },
                    "HS05", Package()
                    {
                        "UsbConnector", 255,
                        "port", Buffer() { 5, 0, 0, 0 },
                    },
                    "HS07", Package()
                    {
                        "UsbConnector", 255,
                        "port", Buffer() { 7, 0, 0, 0 },
                    },
                    "HS08", Package()
                    {
                        "UsbConnector", 255,
                        "port", Buffer() { 8, 0, 0, 0 },
                    },
                    "SSP1", Package()
                    {
                        "UsbConnector", 3,
                        "port", Buffer() { 0xa, 0, 0, 0 },
                    }
                }
            }
        })
    }
}