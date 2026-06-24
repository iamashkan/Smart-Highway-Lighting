using System;
using System.Text;
using UnityEngine;

#if RELIGHTX_MQTTNET
using MQTTnet;
using MQTTnet.Client;
using MQTTnet.Protocol;
#endif

namespace ReLightX
{
    public class MQTTClientBridge : MonoBehaviour
    {
        public string brokerHost = "localhost";
        public int brokerPort = 1883;
        public string clientId = "relightx-unity";
        public bool connectOnStart = true;

        public event Action<string, string> MessageReceived;

#if RELIGHTX_MQTTNET
        private IMqttClient _client;
#endif

        private async void Start()
        {
            if (connectOnStart)
            {
                await Connect();
            }
        }

        public async System.Threading.Tasks.Task Connect()
        {
#if RELIGHTX_MQTTNET
            MqttFactory factory = new MqttFactory();
            _client = factory.CreateMqttClient();
            _client.ApplicationMessageReceivedAsync += args =>
            {
                string topic = args.ApplicationMessage.Topic;
                string payload = Encoding.UTF8.GetString(args.ApplicationMessage.PayloadSegment);
                UnityMainThread.Enqueue(() => MessageReceived?.Invoke(topic, payload));
                return System.Threading.Tasks.Task.CompletedTask;
            };

            MqttClientOptions options = new MqttClientOptionsBuilder()
                .WithTcpServer(brokerHost, brokerPort)
                .WithClientId($"{clientId}-{UnityEngine.Random.Range(1000, 9999)}")
                .Build();
            await _client.ConnectAsync(options);
            await _client.SubscribeAsync("relightx/luminaire/+/brightness");
            await _client.SubscribeAsync("relightx/zone/+/mode");
            await _client.SubscribeAsync("relightx/system/energy");
            await _client.SubscribeAsync("relightx/system/emergency");
            Debug.Log($"ReLight-X MQTT connected to {brokerHost}:{brokerPort}");
#else
            await System.Threading.Tasks.Task.CompletedTask;
            Debug.LogWarning("ReLight-X MQTT bridge running in offline mode. Install MQTTnet and define RELIGHTX_MQTTNET to enable live MQTT.");
#endif
        }

        public async void PublishCommand(string topic, string jsonPayload)
        {
#if RELIGHTX_MQTTNET
            if (_client == null || !_client.IsConnected) return;
            MqttApplicationMessage message = new MqttApplicationMessageBuilder()
                .WithTopic(topic)
                .WithPayload(jsonPayload)
                .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
                .Build();
            await _client.PublishAsync(message);
#else
            await System.Threading.Tasks.Task.CompletedTask;
            Debug.Log($"Offline MQTT publish {topic}: {jsonPayload}");
#endif
        }

        private async void OnDestroy()
        {
#if RELIGHTX_MQTTNET
            if (_client != null && _client.IsConnected)
            {
                await _client.DisconnectAsync();
            }
#else
            await System.Threading.Tasks.Task.CompletedTask;
#endif
        }
    }

    public static class UnityMainThread
    {
        private static readonly System.Collections.Generic.Queue<Action> Actions = new System.Collections.Generic.Queue<Action>();

        public static void Enqueue(Action action)
        {
            lock (Actions)
            {
                Actions.Enqueue(action);
            }
        }

        [RuntimeInitializeOnLoadMethod]
        private static void Init()
        {
            GameObject runner = new GameObject("ReLightX Main Thread Dispatcher");
            runner.AddComponent<UnityMainThreadRunner>();
            UnityEngine.Object.DontDestroyOnLoad(runner);
        }

        private class UnityMainThreadRunner : MonoBehaviour
        {
            private void Update()
            {
                lock (Actions)
                {
                    while (Actions.Count > 0)
                    {
                        Actions.Dequeue()?.Invoke();
                    }
                }
            }
        }
    }
}
