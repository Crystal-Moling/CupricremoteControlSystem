package main

import (
	"encoding/json"
	"fmt"
	"net"
	"runtime"
	"syscall"
	"time"
	"unsafe"
)

func main() {
	connect()
}

func connect() {
	var host string = "127.0.0.1:8088"
	fmt.Println("Trying to connect to " + host)
	addr, err := net.ResolveTCPAddr("tcp4", host)
	checkError(err)

	tcpServer, err := net.DialTCP("tcp4", nil, addr)
	checkError(err)

	majorVersion, minorVersion, buildNumber := RtlGetNtVersionNumbers()
	var versionNumber string = fmt.Sprintf("%d.%d.%d", majorVersion, minorVersion, buildNumber)
	var osDetail string = fmt.Sprintf("%v-%v-%v", runtime.GOOS, versionNumber, runtime.GOARCH)
	jsonBytes, err := json.Marshal(`{ 
			"type": "client",
			"content": ` + osDetail +
		`}`)
	_, err = tcpServer.Write([]byte(jsonBytes))
	checkError(err)
}

func RtlGetNtVersionNumbers() (majorVersion, minorVersion, buildNumber uint32) {
	ntdll := syscall.NewLazyDLL("ntdll.dll")
	procRtlGetNtVersionNumbers := ntdll.NewProc("RtlGetNtVersionNumbers")
	procRtlGetNtVersionNumbers.Call(
		uintptr(unsafe.Pointer(&majorVersion)),
		uintptr(unsafe.Pointer(&minorVersion)),
		uintptr(unsafe.Pointer(&buildNumber)),
	)
	buildNumber &= 0xffff
	return
}

func checkError(err error) {
	if err != nil {
		fmt.Println(err)
		fmt.Println(" - Connection Error, Retry after 5 seconds...")
		time.Sleep(time.Duration(5) * time.Second)
		connect()
	}
}
