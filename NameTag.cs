using System;
using System.Net;
using System.Collections;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Collections.Generic;

public class NameTag : MonoBehaviour
{
    // 주 메서드에서 실행할 작업을 저장하는 큐
    private Queue<System.Action> actionsToExecuteOnMainThread = new Queue<System.Action>();

    // 이동시킬 대상 오브젝트
    public Transform nameTag;
    public Transform blueObject;
    public Transform redObject;

    int s = 0;
    int t = 0;
    
    // 수신할 UDP 포트
    public int udpPort = 5001;

    // UDP 클라이언트 및 수신된 위치 정보를 저장하는 변수
    private UdpClient udpClient;
    private Vector3 receivedPosition;
    private Vector3 previousNameTagPosition;

    private bool isInitialized = false;

    // 스크립트 시작 시 초기화 작업
    void Start()
    {
        // UDP 클라이언트 초기화 및 비동기 수신 시작
        udpClient = new UdpClient(udpPort);
        udpClient.BeginReceive(new AsyncCallback(ReceiveCallback), null);
    }

    // UDP 수신 콜백 메서드
    private void ReceiveCallback(IAsyncResult ar)
    {
        // 송신자의 IP 주소와 포트 정보를 저장하는 객체
        IPEndPoint endPoint = new IPEndPoint(IPAddress.Any, udpPort);

        // 비동기 수신 결과를 바이트 배열로 저장
        byte[] receivedData = udpClient.EndReceive(ar, ref endPoint);

        // 바이트 배열을 문자열로 디코딩
        string receivedString = Encoding.UTF8.GetString(receivedData);

        //Debug.Log("Received: " + receivedString);

        if (receivedString.Equals("r"))
        {
            Debug.Log("Received 'r'");
        }
            
        // 수신된 문자열을 ','로 분리하여 좌표 정보 추출
        string[] pos = receivedString.Split(',');
        float x = float.Parse(pos[0]);
        float y = float.Parse(pos[1]);
        float z = 0; // Z 좌표는 항상 0으로 가정

        s = int.Parse(pos[3]);
        t = int.Parse(pos[4]);

        //Debug.Log("Received: " + receivedString);
        // 추출한 좌표로 Vector3 생성
        receivedPosition = new Vector3(x/200, y/200, z);

        // 다시 비동기 수신 시작
        udpClient.BeginReceive(new AsyncCallback(ReceiveCallback), null);

        // 주 메서드에서 실행할 이동 작업을 큐에 추가
        actionsToExecuteOnMainThread.Enqueue(() => MoveNameTag());
    }
    // 주 메서드에서 실행할 이동 작업을 큐에 추가
    //actionsToExecuteOnMainThread.Enqueue(() => MoveNameTag());

    // 프레임마다 실행되는 업데이트 메서드
    void Update()
    {
        // 주 메서드에서 실행할 모든 작업을 순회하며 실행
        while (actionsToExecuteOnMainThread.Count > 0)
        {
            actionsToExecuteOnMainThread.Dequeue().Invoke();
        }
    }

    // NameTag 이동 메서드
    private void MoveNameTag()
    {
        // Check if s is 9, and reset variables if true
        if (s == 9)
        {
            Debug.Log(s);
            // Reset all relevant variables, positions, and flags
            s = 0;
            t = 0;
            isInitialized = false;
            nameTag.localPosition = Vector3.zero;
            previousNameTagPosition = Vector3.zero;
            blueObject.localPosition = Vector3.zero;
            redObject.localPosition = Vector3.zero;
            blueObject.gameObject.SetActive(true);
            redObject.gameObject.SetActive(true);
            return;  // Exit the method
        }

        // nameTag 오브젝트를 수신된 위치로 이동
        nameTag.localPosition = receivedPosition;

        // If s is 0 and initialization has not occurred yet, perform the initialization
        if (s == 0 && !isInitialized)
        {
            // Initialize previousNameTagPosition with the initial position of nameTag
            previousNameTagPosition = nameTag.localPosition;
            //Debug.Log("Pre:" + previousNameTagPosition);

            // Set the flag to true to indicate that initialization has occurred
            isInitialized = true;
        }

        if (s == 1 && !isInitialized)
        {
            // Initialize previousNameTagPosition with the initial position of nameTag
            previousNameTagPosition = nameTag.localPosition;
            //Debug.Log("Pre:" + previousNameTagPosition);

            // Set the flag to true to indicate that initialization has occurred
            isInitialized = true;
        }
        
        // If s is 0, move the Blue_piette_NakedSingularity object based on the cube's movement
        if (s == 0)
        {
            MoveBlueObject();
        }

        if (s == 1)
        {
            MoveRedObject();
        }

        if (s == -1 )
        {
            blueObject.localPosition = new Vector3(0, 0, 0);
            redObject.localPosition = new Vector3(0, 0, 0);
            isInitialized = false;

        }
    }

        // MoveBlueObject 메서드
    private void MoveBlueObject()
    {
        // Calculate the displacement (change in position) of nameTag
        Vector3 displacement = nameTag.localPosition - previousNameTagPosition;
        //Debug.Log(displacement);
        // Update previousNameTagPosition to the current position of nameTag
        previousNameTagPosition = nameTag.localPosition;

        // Apply the displacement to blueObject
        blueObject.localPosition += displacement;

        // If t is 1, make blueObject invisible
        if (t == 1)
        {
            blueObject.gameObject.SetActive(false);
        }

    }

        private void MoveRedObject()
    {
        // Calculate the displacement (change in position) of nameTag
        Vector3 displacement = nameTag.localPosition - previousNameTagPosition;
        //Debug.Log(displacement);
        // Update previousNameTagPosition to the current position of nameTag
        previousNameTagPosition = nameTag.localPosition;
        
        redObject.localPosition += displacement;
        // If t is 2, make redObject invisible
        if (t == 2)
        {
            redObject.gameObject.SetActive(false);
            //불꽃 재생
        }


    }


    // 스크립트가 파괴될 때 호출되는 메서드
    private void OnDestroy()
    {
        // UDP 클라이언트 닫기
        if (udpClient != null)
        {
            udpClient.Close();
        }
    }
}
