import keycloak from "./keycloak";

function App() {
  const user = keycloak.tokenParsed;

  const callApi = async () => {
    const res = await fetch("http://localhost:8000/protected", {
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    });
    console.log(await res.json());
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>React + Keycloak</h1>
      <p>User: {user?.preferred_username}</p>
      <p>Roles: {user?.realm_access?.roles?.join(", ")}</p>

      <button onClick={callApi}>Call API</button>
      <br /><br />
      <button onClick={() => keycloak.logout()}>
        Logout
      </button>
    </div>
  );
}

export default App;
