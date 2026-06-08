import { useEffect, useMemo, useState } from "react";
import { withApi } from "../../api/http";
import {
  createProduct,
  deleteProduct,
  deleteProductImage,
  listProducts,
  patchProduct,
  setPrimaryProductImage,
  uploadProductImage,
  Product,
} from "../../api/products";

export function ProductsAdmin() {
  const [items, setItems] = useState<Product[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [price, setPrice] = useState("10");
  const [stock, setStock] = useState("1");

  const [busyId, setBusyId] = useState<number | null>(null);

  async function reload() {
    setErr(null);
    try {
      const page = await listProducts({ limit: 100, offset: 0 });
      setItems(page.items);
    } catch (e: any) {
      setErr(e?.error || "LOAD_FAILED");
    }
  }
  useEffect(() => {
    reload();
  }, []);

  function isHidden(p: Product) {
    // логика как в боте: скрытый = in_stock=false (и обычно stock=0)
    return p.in_stock === false;
  }

  async function safeAction(productId: number, fn: () => Promise<void>) {
    setErr(null);
    setBusyId(productId);
    try {
      await fn();
      await reload();
    } catch (e: any) {
      setErr(e?.error || "ACTION_FAILED");
    } finally {
      setBusyId(null);
    }
  }

  async function hideProduct(p: Product) {
    await safeAction(p.id, async () => {
      await patchProduct(p.id, { in_stock: false, stock: 0 });
    });
  }

  async function unhideProduct(p: Product) {
    await safeAction(p.id, async () => {
      await patchProduct(p.id, { in_stock: true });
    });
  }

  async function deleteProductWithConfirm(p: Product) {
    const txt = prompt(`Удалить товар #${p.id} "${p.name}"?\nВведите УДАЛИТЬ для подтверждения:`, "");
    if (txt !== "УДАЛИТЬ") return;

    await safeAction(p.id, async () => {
      await deleteProduct(p.id);
    });
  }

  return (
    <div className="card" style={{ background: "#0b1220" }}>
      <h3 style={{ marginTop: 0 }}>Товары</h3>

      <div className="grid">
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="name" />
        <input className="input" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="price" />
        <input className="input" value={stock} onChange={(e) => setStock(e.target.value)} placeholder="stock" />
        <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="description" />
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <button
          className="btn"
          onClick={async () => {
            setErr(null);
            try {
              await createProduct({
                name,
                description: desc,
                price: Number(price),
                stock: Number(stock),
              });
              setName("");
              setDesc("");
              await reload();
            } catch (e: any) {
              setErr(e?.error || "CREATE_FAILED");
            }
          }}
        >
          Добавить товар
        </button>
        <button className="btn secondary" onClick={reload}>
          Обновить
        </button>
      </div>

      {err && <p style={{ color: "#fca5a5" }}>Ошибка: {err}</p>}

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {items.map((p) => {
          const hidden = isHidden(p);
          const busy = busyId === p.id;

          return (
            <div
              key={p.id}
              className="card"
              style={{
                background: "#111827",
                opacity: hidden ? 0.75 : 1,
                border: hidden ? "1px solid #374151" : "1px solid transparent",
              }}
            >
              <div className="row">
                <b>
                  #{p.id} {p.name}
                </b>
                <span className="spacer" />
                <span className="muted">stock={p.stock}</span>
                <span className="muted">{p.in_stock ? "✅" : "❌"}</span>
              </div>

              {p.primary_image_url && (
                <div style={{ marginTop: 10 }}>
                  <img
                    src={withApi(p.primary_image_url) ?? ""}
                    alt={p.name}
                    style={{ maxWidth: 240, borderRadius: 12, border: "1px solid #1f2937" }}
                  />
                </div>
              )}

              <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
                  <button
                    className="btn secondary"
                    onClick={async () => {
                      const newName = prompt("Новое имя", p.name);
                      if (!newName) return;
                      setErr(null);
                      try {
                        await patchProduct(p.id, { name: newName });
                        await reload();
                      } catch (e: any) {
                        setErr(e?.error || "UPDATE_FAILED");
                      }
                    }}
                  >
                    Переименовать
                  </button>

                  <label className="btn secondary" style={{ cursor: "pointer" }}>
                    Загрузить фото
                    <input
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      onChange={async (e) => {
                        const f = e.target.files?.[0];
                        if (!f) return;
                        setErr(null);
                        try {
                          await uploadProductImage(p.id, f, true);
                          await reload();
                        } catch (ex: any) {
                          setErr(ex?.error || "UPLOAD_FAILED");
                        } finally {
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                  </label>

                  {/* 🙈/👁 скрыть/включить */}
                  {p.in_stock ? (
                    <button
                      className="btn secondary"
                      onClick={async () => {
                        if (!confirm(`Скрыть товар #${p.id}? (in_stock=false, stock=0)`)) return;
                        setErr(null);
                        try {
                          await patchProduct(p.id, { in_stock: false, stock: 0 });
                          await reload();
                        } catch (e: any) {
                          setErr(e?.error || "HIDE_FAILED");
                        }
                      }}
                    >
                      🙈 Скрыть
                    </button>
                  ) : (
                    <button
                      className="btn secondary"
                      onClick={async () => {
                        // вариант: просто включаем
                        // если хочешь, можно попросить stock если он 0
                        setErr(null);
                        try {
                          await patchProduct(p.id, { in_stock: true });
                          await reload();
                        } catch (e: any) {
                          setErr(e?.error || "UNHIDE_FAILED");
                        }
                      }}
                    >
                      👁 Включить
                    </button>
                  )}

                  {/* 🗑 удаление с подтверждением "УДАЛИТЬ" */}
                  <button
                    className="btn"
                      onClick={async () => {
                        const txt = prompt(
                          `Удалить товар #${p.id} "${p.name}"?\nВведите УДАЛИТЬ для подтверждения:`,
                          ""
                        );
                        if (txt !== "УДАЛИТЬ") return;

                        setErr(null);

                        try {
                          // ВАЖНО: у тебя в api/products.ts пока НЕТ deleteProduct - см. ниже
                          await deleteProduct(p.id);
                          await reload();
                        } catch (e: any) {
                          if (e?.status === 409 && e?.error === "PRODUCT_USED_IN_ORDERS") {
                            setErr("Товар нельзя удалить, т.к. он используется в истории заказов.");
                          } else {
                            setErr(e?.error || "DELETE_FAILED");
                          }
                        }
                      }}
                    >
                      🗑 Удалить товар
                  </button>
                </div>

              {!!p.images?.length && (
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  <div className="muted">Изображения:</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                    {p.images.map((img) => (
                      <div key={img.id} className="card" style={{ padding: 10, background: "#0b1220" }}>
                        <img
                          src={withApi(img.url) ?? ""}
                          alt={`img-${img.id}`}
                          style={{ width: 140, height: 140, objectFit: "cover", borderRadius: 10 }}
                        />
                        <div className="row" style={{ marginTop: 8, gap: 8 }}>
                          <button
                            className="btn secondary"
                            disabled={busy || img.is_primary}
                            onClick={async () => {
                              await safeAction(p.id, async () => {
                                await setPrimaryProductImage(p.id, img.id);
                              });
                            }}
                          >
                            {img.is_primary ? "Primary" : "Сделать primary"}
                          </button>
                          <button
                            className="btn"
                            disabled={busy}
                            onClick={async () => {
                              if (!confirm("Удалить изображение?")) return;
                              await safeAction(p.id, async () => {
                                await deleteProductImage(p.id, img.id);
                              });
                            }}
                          >
                            Удалить
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}