const heroText = "Love Actifix - Always Bitches!!!";

const App = () =>
  React.createElement(
    "main",
    { className: "page" },
    React.createElement(
      "div",
      { className: "hero" },
      React.createElement("img", {
        src: "./assets/pangolin.svg",
        alt: "Pangolin illustration",
        className: "pangolin",
      }),
      React.createElement(
        "h1",
        { className: "headline" },
        heroText
      )
    )
  );

const rootEl = document.getElementById("root");
ReactDOM.createRoot(rootEl).render(React.createElement(App));
