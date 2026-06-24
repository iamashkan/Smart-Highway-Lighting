using UnityEngine;

namespace ReLightX
{
    public class PoleManager : MonoBehaviour
    {
        public string poleId;
        public int poleIndex;
        public string zoneId;
        public LuminaireController luminaireA;
        public LuminaireController luminaireB;

        public void Initialize(string id, int index, string zone, float xPosition)
        {
            poleId = id;
            poleIndex = index;
            zoneId = zone;
            transform.position = new Vector3(xPosition, 0f, 0f);
            gameObject.name = poleId;
        }

        public LuminaireController GetLuminaire(string direction)
        {
            return direction == "A" ? luminaireA : luminaireB;
        }
    }
}
